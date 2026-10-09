# SETUP

```
startup.target
  ├─ startup@main.service
  ├─ startup@webcam.service
  ├─ startup@filter.service      one template (startup@.service),
  ├─ startup@printer.service     one instance per module
  └─ startup@file_system.service
        └─ /usr/local/bin/startup.sh <module>
```

## 1. Packages

```
sudo apt update
sudo apt install -y git build-essential pkg-config libsystemd-dev python3 python3-pip python3-venv
git clone https://github.com/Marinku099/Pi-tobooth
```

## 2. Photo directories

```
sudo mkdir -p /var/lib/photobooth/raw /var/lib/photobooth/filtered
sudo chown -R $USER:$USER /var/lib/photobooth
```

## 3. Config

```
sudo mkdir -p /etc/photobooth
sudo cp ~/Pi-tobooth/config.env.example /etc/photobooth/config.env
sudo sed -i 's/\r$//' /etc/photobooth/config.env
```

Format: `KEY=value`, no spaces around `=`, no `export`. New keys go in `config.env.example`

## 4. Install startup files

From the repo root:

```
cd ~/Pi-tobooth
sudo install -m 755 src/system/startup.sh /usr/local/bin/startup.sh
sudo install -m 644 src/system/startup@.service /etc/systemd/system/startup@.service
sudo install -m 644 src/system/startup.target /etc/systemd/system/startup.target
sudo systemctl daemon-reload
```

Re-run after changing any of these files. `git pull` does not update installed copies.

| File | Role |
|---|---|
| `startup.sh` | Runs the module named in `$1` |
| `startup@.service` | Template. `%i` is the module name |
| `startup.target` | Groups all modules |

## 5. Start

```
sudo systemctl enable --now startup.target
systemctl status 'startup@*'
```

Until the real programs replace the `echo` lines in `startup.sh`, each module prints one line and exits. `inactive (dead)` is expected.

## 6. Commands

| Task | Command |
|---|---|
| Start / stop all | `sudo systemctl start startup.target` / `stop` |
| Restart one | `sudo systemctl restart startup@filter` |
| Status of one | `systemctl status startup@filter` |
| Log of one | `journalctl -u startup@filter -f` |
| Log of all | `journalctl -u 'startup@*' -f` |

## 7. Modules

Each team fills in its own row.

| Instance | Team | Branch in `startup.sh` | Setup |
|---|---|---|---|
| `main` | System | TBD | `make` |
| `webcam` | Capture | TBD | `make` |
| `filter` | Filter | `exec /home/<user>/Pi-tobooth/.venv/bin/python3 -u /home/<user>/Pi-tobooth/src/filters/ImageProcessing.py` | venv |
| `printer` | Printer | TBD | `make` |
| `file_system` | Storage | TBD | `make` |

Rules for each branch:
- End with `exec <program>`. No `&`.
- Absolute paths only.
- C: call `setvbuf(stdout, NULL, _IOLBF, 0)` first in `main()`. Python: `python3 -u`. Otherwise logs don't reach `journalctl`.

Python venv:

```
python3 -m venv ~/Pi-tobooth/.venv
~/Pi-tobooth/.venv/bin/pip install -r ~/Pi-tobooth/src/filters/requirements.txt
```

## 8. New module

1. Add a branch in `src/system/startup.sh`.
2. Add `startup@<name>.service` to `Wants=` in `src/system/startup.target`.
3. Repeat step 4.
4. `sudo systemctl restart startup.target`

## 9. Test on a PC or VM

For quick tests without `sudo`, `/var/lib`, or systemd, use the repo's `test/` folder:

```
test/raw_images/        input
test/filtered_images/   output
```

Point the config variables at it and run the program directly:

```
cd ~/Pi-tobooth
export PHOTOBOOTH_RAW_DIR=$PWD/test/raw_images
export PHOTOBOOTH_FILTERED_DIR=$PWD/test/filtered_images
.venv/bin/python3 -u src/filters/ImageProcessing.py
```

In a second terminal, drop in an image under a new name and check the output:

```
cp test/raw_images/Test_Image.jpg test/raw_images/new.jpg
ls test/filtered_images
```

- The watcher only reacts to new files. Existing images in `test/raw_images/` are ignored.
- The exports last for that terminal session only.
- `test/` is for development. The Pi uses `/var/lib/photobooth/`.

## 10. Test the installed pipeline

```
cp test.jpg /var/lib/photobooth/raw/
ls /var/lib/photobooth/filtered
journalctl -u startup@filter -n 20
```

Reboot and run `systemctl status 'startup@*'` to check autostart.

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| `203/EXEC`, "Exec format error" | CRLF or bad shebang: `sudo sed -i 's/\r$//' /usr/local/bin/startup.sh` |
| `203/EXEC`, "Permission denied" | `sudo chmod +x /usr/local/bin/startup.sh` |
| `inactive (dead)` right after start | Branch exits. End it with `exec <program>` |
| Restarts every 5 s | Program is failing: `journalctl -u startup@<name> -n 50` |
| Empty `journalctl` | Output buffering. See step 7 |
| `error` in log | No branch for that module name in `startup.sh` |
| Exit code 127 | Use `python3`, not `python` |
| `ModuleNotFoundError` | Service isn't using the venv's `python3` |
| Config change ignored | `sudo systemctl restart startup@<name>` |

## 12. Uninstall

```
sudo systemctl disable --now startup.target
sudo rm /etc/systemd/system/startup.target /etc/systemd/system/startup@.service /usr/local/bin/startup.sh
sudo systemctl daemon-reload
```
