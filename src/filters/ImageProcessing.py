import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pack.ImageManager import ImageManager
from PIL import Image, UnidentifiedImageError
from gpiozero import LED, Button
from systemd import journal

DIR = os.environ["PHOTOBOOTH_DIR"]
RAW_DIR = os.path.join(DIR, "raw")
FILTERED_DIR = os.path.join(DIR, "filtered")

def wait_until_ready(path, timeout=10, interval=0.2):
    """Wait until the file is unlocked and a complete, readable image."""
    deadline = time.time() + timeout
    while time.time() < deadline:   
        try:
            with open(path, "rb") as f:
                Image.open(f).load()
            return True
        except (PermissionError, OSError, UnidentifiedImageError):
            time.sleep(interval)
    return False

class ExampleHandler(FileSystemEventHandler):

    def on_created(self, event):

        if event.is_directory:
            return

        journal.send(f"New file detected: {event.src_path}")

        if not wait_until_ready(event.src_path):
            journal.send(f"Skipped (file never became readable): {event.src_path}")
            return

        image = ImageManager()
        image.read(event.src_path)

        Filter(image)

        filename = os.path.basename(event.src_path)
        output_path = os.path.join(FILTERED_DIR, filename)

        image.write(output_path)

        journal.send("Finished processing and saved to filtered_images.")


observer = Observer()
event_handler = ExampleHandler()

observer.schedule(
    event_handler,
    path=RAW_DIR,
    recursive=False
)

# =========================
# Filter System
# =========================

Num = 0

def Filter(image):
    match Num:
        case 1:
            Filter1(image)
        case 2:
            Filter2(image)
        case 3:
            Filter3(image)
        case _:
            Filter0(image)


def ChangeFilter():
    global Num
    Num += 1

    if Num >= 4:
        Num = 0

    journal.send(f"Current Filter: {Num}")

    # LED_Active(Num)

# Red    = LED(17)
# Yellow = LED(27)
# Blue   = LED(22)

# def LED_Active(N):
#     Red.off()
#     Yellow.off()
#     Blue.off()

#     match N:
#         case 1: Red.on()
#         case 2: Yellow.on()
#         case 3: Blue.on()


# =========================
# Filters
# =========================

def Filter0(image):

    # image.convertToEdgeBinary(50, 0, 100)
    image.convertToGrayscale()

    journal.send("Filter 0")


def Filter1(image):

    Filter0(image)

    journal.send("Filter 1")


def Filter2(image):

    Filter0(image)

    journal.send("Filter 2")


def Filter3(image):
    image.convertToPencilSketch()

    journal.send("Filter 3: Pencil Sketch")

# =========================
# Main
# =========================

# button = Button(5, bounce_time=0.2)

def main():
    # button.when_pressed = ChangeFilter
    observer.start()

    try:
        journal.send("Start")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        observer.stop()

        journal.send("Observer stopped.")

    observer.join()

main()