#!/bin/sh
# Called by startup@.service as: startup.sh <module>
case $1 in
        "main")
                echo "running main"
                ;;
        "webcam")
                echo "running webcam module"
                ;;
        "filter")
                echo "running filter module"
                ;;
        "printer")
                echo "running printer module"
                ;;
        "file_system")
                echo "running file system module"
                ;;
        *)
                echo "error"
                ;;
esac
