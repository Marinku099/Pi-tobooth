#!/bin/sh
# Called by startup@.service as: startup.sh <module>
case $1 in
        "main")
                echo "running main"
                ;;
        "webcam")
                echo "running webcam module"
                exec /usr/local/bin/webcam
                ;;
        "filter")
                echo "running filter module"
                exec /home/punchichi/Pi-tobooth/.venv/bin/python3 -u /home/punchichi/Pi-tobooth/src/filters/ImageProcessing.py
                ;;
        "printer")
                echo "running printer module"
                ;;
        "file_system")
                echo "running file system module"
                exec /usr/local/bin/storage
                ;;
        *)
                echo "error"
                ;;
esac
