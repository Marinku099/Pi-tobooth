cd ~/Pi-tobooth
SERVICE="startup@filter.service"
echo "===== ก่อนบังคับหยุด ====="
sudo systemctl show "\$SERVICE" \
-p ActiveState -p SubState -p MainPID -p NRestarts
BEFORE=\$(sudo systemctl show "\$SERVICE" -p NRestarts -value)
echo "===== บังคับหยุด Filter ====="
sudo systemctl kill -kill-who main--signal SIGKILL "\$SERVICE"
sleep 7
echo "===== หลังเริ่มใหม่ ====="
sudo systemctl show "\$SERVICE" \
-p ActiveState -p SubState -p MainPID -p NRestarts
AFTER=\$(sudo systemctl show "\$SERVICE" -p NRestarts --value)
echo "Restart count before: \$BEFORE"
echo "Restart count after: \$AFTER"
echo "===== Filter log ====="
sudo journalctl -u "\$SERVICE" -n 30 --no-pager

STAMP=\$(date +%s)
NAME="FR210_recovery_\${STAMP}.jpg"
sudo cp "\$HOME/Pi-tobooth/test/raw_images/Test_Image.jpg" \
"/var/lib/photobooth/raw/\$NAME"
for i in \$(seq 1 20); do
if sudo test -s "/var/lib/photobooth/filtered/\$NAME"; then
break
fi
sleep 1
done
if sudo test -s "/var/lib/photobooth/filtered/\$NAME"; then
echo "PASS: พบภาพผลลัพธ์ \$NAME"
else
echo "FAIL: ไม่พบภาพผลลัพธ์ \$NAME"
fi
sudo systemctl is-active "\$SERVICE"

cd ~/Pi-tobooth
rm -rf /tmp/fr219-src
mkdir -p /tmp/fr219-src

git archive origin/system src/storage | tar -x -C /tmp/fr219-src

make -C/tmp/fr219-src/src/storage
echo "Build exit code: \$?"

cd ~/Pi-tobooth
STORAGE=/tmp/fr219-src/src/storage/storage
echo "===== ตรวจ Storage executable ====="
Is- "\$STORAGE"
echo "===== กรณีกำหนด PHOTOBOOTH_DIR ====="
rm -rf /tmp/fr210-fs-normal
mkdir -p /tmp/fr210-fs-normal
timeout 3s env PHOTOBOOTH_DIR=/tmp/fr210-fs-normal \
"\$STORAGE" > /tmp/fr210-fs-normal.log 2>&1
RC=\$?
cat /tmp/fr210-fs-normal.log
echo "Normal case exit code: \$RC"

timeout 3s env -u PHOTOBOOTH DIR \
/tmp/fr219-src/src/storage/storage \
> /tmp/fr210-fs-unset.log 2>&1
RC=\$?
cat /tmp/fr210-fs-unset.log
echo "Unset case exit code: \$RC"

echo "===== startup.sh ====="
sudo sed -n '1,240p' /usr/local/bin/startup.sh
sudo bash -n /usr/local/bin/startup.sh
echo "Syntax check exit code: \$?"

sudo bash -x /usr/local/bin/startup.sh main \
> /tmp/fr210-main.log 2>&1
MAIN_RC=\$?
cat /tmp/fr210-main.log
echo "Main exit code: \$MAIN RC"

sudo bash -x /usr/local/bin/startup.sh printer \
> /tmp/fr210-printer.log 2>&1
PRINTER RC=\$?
cat /tmp/fr210-printer.log
echo "Printer exit code: \$PRINTER RC"

echo "===== คำสั่งใน startup.sh ====="
grep -nE 'webcam storage/main printer|file_system python exec' \
/usr/local/bin/startup.sh
echo "===== Webcam executable ====="
if [ -x/usr/local/bin/webcam ]; then
echo "พบ /usr/local/bin/webcam"
else
echo "ไม่พบหรือเรียก /usr/local/bin/webcam ไม่ได้"
fi
echo "===== Storage executable ในโปรเจกต์ ====="
if [ -x~/Pi-tobooth/src/storage/storage ]; then
echo "พบ ~/Pi-tobooth/src/storage/storage"
else
echo "ไม่พบหรือเรียก Storage binary ไม่ได้"
fi
echo "===== ไฟล์กล้องและ Storage ใน source ====="
find ~/Pi-tobooth/src-type f \
 (-iname 'cam' -o-iname 'storage' -o -iname 'Makefile' \) \
-print