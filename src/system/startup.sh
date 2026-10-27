#!/bin/sh
# Called by startup@.service as: startup.sh <module>
case $1 in

        "webcam")
                echo "running webcam module"
                exec /usr/local/bin/webcam
                ;;
	"button")
		echo "button"
		        
		;;
	"filter")
                echo "running filter module"
		#exec /home/punchichi/Pi-tobooth/.venv/bin/python3 -u /home/punchichi/Pi-tobooth/src/filters/ButtonLed.py
                exec /home/punchichi/Pi-tobooth/.venv/bin/python3 -u /home/punchichi/Pi-tobooth/src/filters/ImageProcessing.py                ;;
        "printer")
                echo "running printer module"
                exec /home/punchichi/Pi-tobooth/.venv/bin/python3 -u /home/punchichi/Pi-tobooth/src/printer/start.py
                ;;
        "file_system")
                echo "running file system module"
                exec /usr/local/bin/storage
                ;;
        *)
                echo "error"
                ;;
esac
