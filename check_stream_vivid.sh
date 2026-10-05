#!/bin/bash
for i in 1 2 3 4 5; do
    echo "=== vivid รอบที่ $i ==="
    timeout 5 v4l2-ctl -d /dev/video2 --stream-mmap --stream-count=5   # แทน X ด้วย node vivid ที่เป็น Video Capture
    echo "exit code: $?"
done
