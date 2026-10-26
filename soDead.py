# Stage : Start up -> { Take A Photo || Select Filter }-> Print

import platform
from gpiozero import LED, Button ,Device
from time import sleep

# from signal import pause

if platform.system() == "Windows":
    from gpiozero.pins.mock import MockFactory, MockPin
    Device.pin_factory = MockFactory()


led1 = LED(17)  # GPIO17 : 11
led2 = LED(27)  # GPIO27 : 13
led3 = LED(22)  # GPIO22 : 15
BT1 = Button(5)  # GPIO5 : 29
BT2 = Button(6)  # GPIO6 : 31
num = 0

def LED_Set(a,b,c): # a,b,c = int 0-1 | 0=low 1=high can be in range 0-1 for light power
    try:
        led1.value = a
        led2.value = b
        led3.value = c
    except ValueError:
        print(ValueError)

def LED_TakeAPic():
    LED_Set(0,0,0); sleep(0.2)
    LED_Set(1,0,0); sleep(0.5)
    LED_Set(1,1,0); sleep(0.5)
    LED_Set(1,1,1); sleep(0.5)
    print("TAKE A PICTURE")
    
def LED_ChageFilter(numFilter):
    match numFilter:
        case 0:
            # led1.off
            # led2.off
            # led3.off
            # new tech
            # LED_Set(0,0,0)
            print("000")
        case 1:
            # LED_Set(1,0,0)
            print("100")
        case 2:
            # LED_Set(0,1,0)
            print("010")
        case 3:
            # LED_Set(0,0,1)
            print("001")
        case _:
            print("unknow")

def chageFilter():
    global num
    num += 1
    if num>=4:
        num=0
print("start")
sleep(10)
print("end")
while True:
    test  = input("what you want to DO? : ")
    match test:
        case "a":
            LED_TakeAPic()
        case "s":
            chageFilter()
            LED_ChageFilter(num)
        case "d":
            break
        case _:
            print("unknow")
            

    if BT1.is_pressed:
        # call Take a pic FROM AON code
        LED_TakeAPic()
    elif BT2.is_pressed:
        # call Change Filter FROM IAUM code
        chageFilter()
        LED_ChageFilter(num)
        
# pause()        