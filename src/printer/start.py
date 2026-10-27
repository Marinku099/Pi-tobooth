#!/usr/bin/env python3
"""
Persistent printer: keep a connection open and print files dropped into a queue directory.

Type "stop" (then Enter) in this terminal to stop the script gracefully (same as Ctrl+C).
"""

import asyncio
import os
import shutil
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from timiniprint.devices import PrinterCatalog
from timiniprint.transport.bluetooth import BluetoothDiscovery, BleakBluetoothConnector
from timiniprint.printing.connected import connect_printer
from timiniprint.printing.settings import PrintSettings
from timiniprint.printing.errors import PrinterNotReadyError

from systemd import journal

# === Config ===
PRINTER_NAME: Optional[str] = "MXW-W5"  # e.g. "MX-W5" or None to auto-select first supported
QUEUE_DIR = Path("print_queue")
# PRINTED_DIR = Path("printed")
FAILED_DIR = Path("failed")

PRINT_INTERVAL_SECONDS = 3.0
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5.0
BLACKENING = 5
CONNECT_BACKOFF = 1.0
MAX_CONNECT_BACKOFF = 60.0
# ==============


async def connect_and_keep(catalog, discovery, stop_event: asyncio.Event):
    backoff = CONNECT_BACKOFF
    while not stop_event.is_set():
        try:
            if PRINTER_NAME:
                journal.send(f"[+] Resolving printer named {PRINTER_NAME} ...")
                device = await discovery.resolve_device(PRINTER_NAME)
            else:
                journal.send("[+] Auto-resolving first supported print.sender ...")
                device = await discovery.resolve_device(None)

            if device is None:
                journal.send(f"[!] No supported printer found; retrying in {backoff}s")
                await asyncio.wait([stop_event.wait()], timeout=backoff)
                backoff = min(MAX_CONNECT_BACKOFF, backoff * 2)
                continue

            journal.send(f"[+] Connecting to {device.display_name or device.profile_key} ...")
            connected = await connect_printer(device, BleakBluetoothConnector())
            journal.send("[+] Connected.")
            return connected

        except Exception as exc:
            journal.send(f"[!] Connect failed: {exc}")
            # Wait with cancellation support
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=backoff)
                # stop_event set -> exit
                break
            except asyncio.TimeoutError:
                backoff = min(MAX_CONNECT_BACKOFF, backoff * 2)
                continue
    return None


async def try_print_with_retries(connected, path: Path) -> Tuple[bool, Exception | None]:
    """
    Try to print path up to MAX_RETRIES times.
    Returns (True, None) on success, (False, exc) on terminal failure.
    """
    last_exc = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            settings = PrintSettings(blackening=BLACKENING)
            await connected.print_file(str(path), settings=settings)
            return True, None

        except PrinterNotReadyError as pne:
            last_exc = pne
            journal.send(f"[!] PrinterNotReadyError on {path.name} attempt {attempt}: {pne}")

        except Exception as exc:
            last_exc = exc
            journal.send(f"[!] Error printing {path.name} attempt {attempt}: {exc}")

        if attempt < MAX_RETRIES:
            journal.send(f"[i] Waiting {RETRY_DELAY_SECONDS}s before retrying {path.name} (attempt {attempt + 1})")
            await asyncio.sleep(RETRY_DELAY_SECONDS)

    return False, last_exc


# async def stdin_watcher(stop_event: asyncio.Event):
#     """
#     Watch stdin for the word 'stop' (case-insensitive). When seen, set stop_event.
#     Uses a thread to avoid blocking the asyncio event loop.
#     """
#     loop = asyncio.get_event_loop()
#     while not stop_event.is_set():
#         try:
#             # Use blocking readline in a thread so we don't block the event loop
#             line = await asyncio.to_thread(sys.stdin.readline)
#             if not line:
#                 # EOF (e.g., stdin closed) -> set stop and break
#                 stop_event.set()
#                 break
#             if line.strip().lower() == "stop":
#                 journal.send("[*] Stop command received via stdin.")
#                 stop_event.set()
#                 break
#         except Exception:
#             # If anything goes wrong reading stdin, don't crash watcher; set stop and exit
#             stop_event.set()
#             break


async def main_loop(stop_event: asyncio.Event):
    QUEUE_DIR.mkdir(exist_ok=True)
    # PRINTED_DIR.mkdir(exist_ok=True)
    FAILED_DIR.mkdir(exist_ok=True)

    catalog = PrinterCatalog.load()
    discovery = BluetoothDiscovery(catalog)

    connected = None

    try:
        while not stop_event.is_set():
            if connected is None:
                connected = await connect_and_keep(catalog, discovery, stop_event)
                if connected is None:
                    # stop_event likely set or connection couldn't be made
                    break

            # list files (stable snapshot)
            try:
                files = sorted(p for p in QUEUE_DIR.iterdir() if p.is_file())
            except Exception as e:
                journal.send(f"[!] Error listing queue directory: {e}")
                files = []

            if not files:
                # wait a short while or until stop_event
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                else:
                    break

            for f in files:
                if stop_event.is_set():
                    break

                journal.send(f"[>] Found file to print: {f.name}")

                success, err = await try_print_with_retries(connected, f)

                if success:
                    os.remove(os.path.join(QUEUE_DIR, f.name));
                    # target = PRINTED_DIR / f.name
                    # shutil.move(str(f), str(target))
                    journal.send(f"[√] Printed -> {f.name}")
                    if PRINT_INTERVAL_SECONDS > 0:
                        # allow interruption while sleeping
                        try:
                            await asyncio.wait_for(stop_event.wait(), timeout=PRINT_INTERVAL_SECONDS)
                            break
                        except asyncio.TimeoutError:
                            pass
                    continue

                # failure handling
                journal.send(f"[!] Failed to print {f.name}: {err}")

                if not isinstance(err, PrinterNotReadyError):
                    # likely connection issue; disconnect and reconnect next loop
                    try:
                        await connected.disconnect()
                    except Exception:
                        pass
                    connected = None

                    failed_target = FAILED_DIR / f"{int(time.time())}_{f.name}"
                    try:
                        shutil.move(str(f), str(failed_target))
                    except Exception as e:
                        journal.send(f"[!] Could not move failed file {f.name}: {e}")
                    journal.send(f"[!] Moved to failed: {failed_target} and will reconnect")
                    break  # break file loop to attempt reconnect

                # Printer reported a fault (paper out / cover open / overheated etc.)
                failed_target = FAILED_DIR / f"{int(time.time())}_{f.name}"
                try:
                    shutil.move(str(f), str(failed_target))
                except Exception as e:
                    journal.send(f"[!] Could not move failed file {f.name}: {e}")
                journal.send(f"[!] Printer reported fault; moved to failed: {failed_target}")

            # small delay to avoid busy-loop; allow interrupt
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

    except asyncio.CancelledError:
        pass
    finally:
        if connected is not None:
            try:
                journal.send("[*] Disconnecting...")
                await connected.disconnect()
            except Exception:
                pass


def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stop_event = asyncio.Event()

    # make Ctrl+C and SIGTERM set stop_event
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(s, stop_event.set)
        except NotImplementedError:
            # Windows or restricted environments may not support add_signal_handler
            pass

    # create tasks
    main_task = loop.create_task(main_loop(stop_event))
    #stdin_task = loop.create_task(stdin_watcher(stop_event))

    try:
        loop.run_until_complete(asyncio.gather(main_task))#, stdin_task))
    except KeyboardInterrupt:
        # fallback for platforms where signal handling isn't wired up
        stop_event.set()
        # wait a moment for graceful shutdown
        try:
            loop.run_until_complete(asyncio.wait_for(main_task, timeout=5.0))
        except Exception:
            pass
    finally:
        # cancel remaining tasks and close loop
        for t in asyncio.all_tasks(loop):
            if not t.done():
                t.cancel()
        try:
            loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True))
        except Exception:
            pass
        loop.close()
        journal.send("[*] Exited.")


if __name__ == "__main__":
    run()
