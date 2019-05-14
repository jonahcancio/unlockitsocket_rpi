
#!/usr/bin/env python
import requests
import signal
import time
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
#import sys
#sys.path.append('/home/pi/Desktop/MFRC522-python')

class Timeout():#class for timeout of input
    class Timeout(Exception):
        pass
    
    def __init__(self,sec):
        self.sec = sec
        
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)
    
    def __exit__(self, *args):
        signal.alarm(0)
        
    def raise_timeout(self, *args):
        raise Timeout.Timeout()


reader = SimpleMFRC522()

cardSlot = False
prevCard = -1
timeLeft = 0
timeLastChecked = 0

while(True):
    print("Hold a tag near the reader")
    try:
        with Timeout(5):
            id, text = reader.read()#read RFID card
            
            #check if this is same card as before
            if(id == prevCard):
                print(id)
                print("In Use")
                
                if(timeLeft > 0):#decrement time left
                    print("Time Left: " + str(timeLeft))
                    timePassed = time.time() - timeLastChecked
                    timeLeft = timeLeft - timePassed
                    timeLastChecked = time.time()
                else:
                    print("No balance left")
                    patch = requests.patch('https://unlockitsocketapp.herokuapp.com/api/simple/students/' + str(id) +'/', data= {"is_using": False})
                    prevCard = -1

                
            else:#if not request from server
                print(id)
                print("New card")
                response = requests.get('https://unlockitsocketapp.herokuapp.com/api/simple/students/' + str(id) +'/')
                print(response.json())
                timeLeft = response.json()["balance"]
                print(timeLeft)
                #timeLeft = 10
                patch = requests.patch('https://unlockitsocketapp.herokuapp.com/api/simple/students/' + str(id) + '/', json= {"is_using": True})
                
                timeLastChecked = time.time()
                prevCard = id
                print(prevCard)
            
        #print(id)
        #print(text)
    except Timeout.Timeout:
        if(prevCard > 0):
            patch = requests.patch('https://unlockitsocketapp.herokuapp.com/api/simple/students/' + str(id) +'/', json= {"is_using": False})
        else:
            print("No card in slot")
        prevCard = -1
        
    finally:
        GPIO.cleanup()
