# Stage : Start up -> { Take A Photo || Select Filter }-> Print

import subprocess
import platform # just some module that can make me run on window :C
from gpiozero import LED, Button ,Device
from time import sleep
# from signal import pause
from systemd import journal
import sys
import signal

# check where you are
ON_WINDOWS = platform.system() == "Windows"


# no need this code when run on RASPBERRY PI
#if ON_WINDOWS :
 #   from gpiozero.pins.mock import MockFactory, MockPin
  #  Device.pin_factory = MockFactory()
  

# Define led and button {logical pin : physical pin}
led1 = LED(17)  # GPIO17 : 11
led2 = LED(27)  # GPIO27 : 13
led3 = LED(22)  # GPIO22 : 15
BT1 = Button(5, bounce_time=0.1)  # GPIO5 : 29
BT2 = Button(6, bounce_time=0.1)  # GPIO6 : 31
num = 0


# ทางผ่านเฉยๆ
def SIGNAL_Send(*command):
    #if ON_WINDOWS:
    #   print("I am stuck on WINDOWS")
    #    return
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("error signal fail :" ," ".join(command))
        print("error detail : ",result.stderr.strip())


# Function to set up LED light(?)
# a,b,c = int 0-1 | 0=low 1=high can be in range 0-1 for light power |**larpest man alive**| if want to do 0-1 need to use PDWPin
def LED_Set(a,b,c): 
    try:
        led1.value = a
        led2.value = b
        led3.value = c
    except ValueError:
        print(ValueError)


def LED_TakeAPic():
    journal.send("Take A pic")
    LED_Set(0,0,0); sleep(1)
    LED_Set(1,0,0); sleep(1)
    LED_Set(1,1,0); sleep(1)
    print("TAKE A PICTURE")
    # LED_Set(1,1,1); sleep(1)
    # subprocess.run(["pkill","USR1","-X","webcam"]) # run command on terminal to send SUGUSR1
    SIGNAL_Send("pkill","-USR1","-x","webcam")
    LED_Set(1,1,1); sleep(3)
    sleep(0.2)
    LED_Show()
    
    
def LED_Show():
    journal.send("SHOW LED")
    # subprocess.run(["pkill","USR1","-f","python3.*ImageProcessing.py"])
    # chageFilter()
    match num:
        case 0:
            LED_Set(0,0,0)
            print("000")
        case 1:
            LED_Set(1,0,0)
            print("100")
        case 2:
            LED_Set(0,1,0)
            print("010")
        case 3:
            LED_Set(0,0,1)
            print("001")
        case _:
            print("unknow")
    #print(f"  Filter {num}: {int(led1.value)}{int(led2.value)}{int(led3.value)}")


def LED_chageFilter():
    journal.send("now num is")
    global num
    num += 1
    if num>=4:
        num=0
    LED_Show()
    SIGNAL_Send("pkill","-USR1","-f","python3.*ImageProcessing.py")


# test some on window
def press(button):
    button.pin.drive_low()
    sleep(0.05)
    button.pin.drive_high()
    sleep(0.05)
    
def shutdown_seq():
    journal.send("Received SIGTERM, turn off LEDs")
    BT1.when_pressed = None
    BT2.when_pressed = None
    
    LED_Set(0,0,0)
    
def handle_sigterm(signum, frame):
    shutdown_seq();
    sys.exit(0)
    
def main():
    journal.send("start button")
    signal.signal(signal.SIGTERM, handle_sigterm)
    # set button when pres to call function        
    BT1.when_pressed = LED_TakeAPic
    BT2.when_pressed = LED_chageFilter
    
    # set up LED when start
    LED_Set(0,0,0)
    # LED_ChageFilter()
    
    # try catch FROM "CLUAD"
    try:
        #if ON_WINDOWS:
        #   press(BT1)
        #else :
        while True:             # รอปุ่มไปเรื่อยๆ (gpiozero เรียกฟังก์ชันให้เอง)
            sleep(1)
    except KeyboardInterrupt:  # กด Ctrl+C
        pass
    finally:
        print("end")
        shutdown_seq();
        
main()      
