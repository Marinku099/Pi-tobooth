#!/bin/bash

for i in 0 1 2 3; do
    echo "=== /dev/video$i ==="
    v4l2-ctl -d /dev/video$i --info | grep -E "Driver name|Card type|Video Capture"
done
