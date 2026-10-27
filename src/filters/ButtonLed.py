# Stage : Start up -> { Take A Photo || Select Filter }-> Print

import subprocess
import platform # just some module that can make me run on window :C
from gpiozero import LED, Button ,Device
from time import sleep
from signal import pause

# check where you are
ON_WINDOWS = platform.system() == "Windows"


# no need this code when run on RASPBERRY PI
if ON_WINDOWS :
    from gpiozero.pins.mock import MockFactory, MockPin
    Device.pin_factory = MockFactory()


# Define led and button {logical pin : physical pin}
led1 = LED(17)  # GPIO17 : 11
led2 = LED(27)  # GPIO27 : 13
led3 = LED(22)  # GPIO22 : 15
BT1 = Button(5, bounce_time=0.5)  # GPIO5 : 29
BT2 = Button(6, bounce_time=0.5)  # GPIO6 : 31
num = 0


# ทางผ่านเฉยๆ
def SIGNAL_Send(command):
    if ON_WINDOWS:
        print("I am stuck on WINDOWS")
        return
    result = subprocess.run(command, capture_output=True, text=True, runtime = 1)
    if result != 0:
        print("error signal fail :" ," ".join(result))


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
    subprocess.run(["sudo","pkill","USR1","-X","webcam"]) # run command on terminal to send SUGUSR1
    LED_Set(0,0,0); sleep(0.2)
    LED_Set(1,0,0); sleep(0.5)
    LED_Set(1,1,0); sleep(0.5)
    LED_Set(1,1,1); sleep(0.5)
    print("TAKE A PICTURE")
    sleep(0.2)
    LED_ChageFilter(num)
    
    
def LED_ChageFilter():
    subprocess.run(["sudo","pkill","USR1","-f","ImageProcessing"])
    chageFilter()
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
    print(f"  Filter {num}: {int(led1.value)}{int(led2.value)}{int(led3.value)}")


def chageFilter():
    global num
    num += 1
    if num>=4:
        num=0


# test some on window
def press(button):
    button.pin.drive_low()
    sleep(0.05)
    button.pin.drive_high()
    sleep(0.05)
    
    
def main():
    print("start")
    # set button when pres to call function        
    BT1.when_pressed = LED_TakeAPic
    BT2.when_pressed = LED_ChageFilter
    
    # set up LED when start
    LED_Set(0,0,0)
    LED_ChageFilter(num)
    
    # try catch FROM "CLUAD"
    try:
        if ON_WINDOWS:
            asdasdasd()
        else :
            while True:             # รอปุ่มไปเรื่อยๆ (gpiozero เรียกฟังก์ชันให้เอง)
                sleep(1)
    except KeyboardInterrupt:       # กด Ctrl+C
        pass
    finally:
        print("end")
        LED_Set(0,0,0)


if __name__ == "__main__":
    main()      