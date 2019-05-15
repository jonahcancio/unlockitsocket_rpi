import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from gpiozero import LED

import signal
import time

import requests

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


# actuators
reader = SimpleMFRC522()
unlockitSocket = LED(21)


# card values
currentCard = 0
registeredCard = 0
timeLoggedIn = 0
loginBalance = 0
balanceLeft = 0

# flags
isLoginPatching = False
isLogoutPatching = False



def attempt_login(url):
    global timeLoggedIn, loginBalance
    print("attempting login...")
    response = requests.patch(url, json={'is_using': True})    
    print(response.json())
    if response.status_code == 200:
        print("LOGIN SUCCESS: your card is valid")
        timeLoggedIn = time.time()
        loginBalance = response.json()['balance']
        actuate_login() 
    else:
        print("LOGIN FAILED: invalid card")


def actuate_login():
    global balanceLeft, registeredCard, unlockitSocket
    balanceLeft = loginBalance
    registeredCard = currentCard
    if balanceLeft > 0:
        unlockitSocket.on()

def attempt_logout(url):
    print("attempting logut...")
    response = requests.patch(url, json={'balance': int(balanceLeft), 'is_using': False})
    print(response.json())
    if response.status_code == 200:
        actuate_logout()
        print("LOGOUT SUCCESS")
    else:
         print("LOGOUT FAILED")
    
def actuate_logout():
    global registeredCard, loginBalance, balanceLeft
    registeredCard = 0
    loginBalance = 0
    balanceLeft = 0
    unlockitSocket.off()
    


def main():
    global currentCard, registeredCard, timeLoggedIn, balanceLeft
    while True:
        try:
            with Timeout(1):
                currentCard = 0
                print("reading card...")
                currentCard, cardText = reader.read()
                print("Card Found: {}".format(currentCard))
                time.sleep(1)
        except:
            if currentCard == 0:
                print("No Card")
        finally:
            GPIO.cleanup()
        
        # handle login if new card found
        if registeredCard == 0 and currentCard != registeredCard:
            #if not isLoginPatching:
                attempt_login('https://unlockitsocketapp.herokuapp.com/api/simple/students/{}/'.format(currentCard))
                
        # handle logout if registered card is no more
        elif registeredCard > 0 and currentCard != registeredCard:
            #if not isLogoutPatching:
                attempt_logout('https://unlockitsocketapp.herokuapp.com/api/simple/students/{}/'.format(registeredCard))
        
        # handle balance calculations
        if registeredCard > 0:
            balanceLeft = loginBalance - (time.time() - timeLoggedIn)
            balanceLeft = balanceLeft if balanceLeft > 0 else 0
            print("Balance left: {}".format(balanceLeft))
            if balanceLeft <= 0:
                print("YOUR TIME IS UP, PINHEAD!")
                attempt_logout('https://unlockitsocketapp.herokuapp.com/api/simple/students/{}/'.format(registeredCard))
            
            
        
main()


