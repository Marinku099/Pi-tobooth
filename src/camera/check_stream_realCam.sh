#!/bin/bash
for i in 1 2 3 4 5; do
    echo "=== รอบที่ $i ==="
    timeout 5 v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=5
    echo "exit code: $?"
done
