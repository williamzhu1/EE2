import time
import requests
import RPi.GPIO as GPIO
import requests
from gpiozero import TonalBuzzer
from gpiozero import DigitalInputDevice
from gpiozero import Servo
from gpiozero.tones import Tone
from mfrc522 import SimpleMFRC522

buzzer = TonalBuzzer(18)
hall=DigitalInputDevice(4)
reader = SimpleMFRC522()
# Modified for servo
myServo = Servo(17, frame_width=0.025, min_pulse_width=0.0005, max_pulse_width=0.0045)

def play_buzzer():
    print("Bike stolen!")
    buzzer.play(Tone("A5"))


while True:
    response = requests.get('https://studev.groept.be/api/a22ib2d02/getMode')
    if response.status_code == 200:
        try:
            # Extract the mode from the response
            data = response.json()
            mode = data[0]['mode']
            name = data[0]['name']
            lockStatus = data[0]['isLocked']
            AlarmStatus = data[0]['isAlarming']
        except KeyError:
            print('Error: Response JSON does not contain a "mode" field')
    else:
        print('Error: Could not retrieve mode from API endpoint')

    if mode == 0:
        print('Read Mode')
        if(lockStatus == 1):
            if(hall.value == 1):
                hey=requests.get('https://studev.groept.be/api/a22ib2d02/Alarm')
            if(hall.value == 0):
                hey=requests.get('https://studev.groept.be/api/a22ib2d02/notAlarm')
            if AlarmStatus == 1:
                play_buzzer()
            else:
                print("STOP")
                buzzer.stop()
        else:
            buzzer.stop()
            hey=requests.get('https://studev.groept.be/api/a22ib2d02/notAlarm')
        status, TagType = reader.read_no_block()
        print(status)
        if str(status) == 'None':
            print("No Card Found")
        elif status != 'None':
            scanned = requests.get('https://studev.groept.be/api/a22ib2d02/scan/' + str(status))
            if scanned.status_code == 200:
                try:
                    # Extract the mode from the response
                    scannedActive = scanned.json()
                    if scannedActive and len(scannedActive) > 0:
                        active = scannedActive[0]['isActive']
                        print(active)
                    else:
                        print('Error: Response JSON is empty')
                        scanNULL = requests.get('https://studev.groept.be/api/a22ib2d02/scanNULL/' + str(status))
                        active = 0
                except KeyError:
                    print('Error: Response JSON does not contain a "isActive" field')
            else:
                print('Error: Could not retrieve mode from API endpoint')
            if(active == 1):
                tm = str(int(time.time()))
                if(lockStatus == 1):
                    # Modified for servo
                    myServo.max()
                    time.sleep(0.5)
                    myServo.mid()
                    time.sleep(0.5)
                    myServo.min()
                    time.sleep(0.5)
                    print("Unlock")
                    access = requests.get("https://studev.groept.be/api/a22ib2d02/scanHistory/" + \
                                          str(status) + "/" + tm + "/1")
                    unlock = requests.get("https://studev.groept.be/api/a22ib2d02/unlock")
                else:
                    # Modified for servo
                    myServo.min()
                    time.sleep(0.5)
                    myServo.mid()
                    time.sleep(0.5)
                    myServo.max()
                    time.sleep(0.5)
                    print("Lock")
                    access = requests.get("https://studev.groept.be/api/a22ib2d02/scanHistory/" + \
                                          str(status) + "/" + tm + "/2")
                    lock = requests.get("https://studev.groept.be/api/a22ib2d02/lock")
            else:
                print("Unauthorized access")
                tm = str(int(time.time()))
                access = requests.get("https://studev.groept.be/api/a22ib2d02/scanHistory/" + \
                                      str(status) + "/" + tm + "/0")

    elif mode == 1:
        buzzer.stop()
        hey=requests.get('https://studev.groept.be/api/a22ib2d02/notAlarm')
        print('Write Mode')
        print("Now place your tag to write")
        id, tagType = reader.read()
        print(id)
        print(name)
        addCard = requests.get('https://studev.groept.be/api/a22ib2d02/addCard/'+ str(id) + '/' + name + '/'+ name)
        print('https://studev.groept.be/api/a22ib2d02/addCard/'+ str(id) + '/' + name + '/'+ name)
        print(addCard.json())
        print("Written")
        setRead = requests.get('https://studev.groept.be/api/a22ib2d02/readMode')
        print(setRead.json())
    else:
        print('Invalid mode')

    print("One cycle")
