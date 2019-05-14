import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from gpiozero import LED

import signal
import time

import asyncio
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


reader = SimpleMFRC522()
unlockitSocket = LED(21)


# card values
currCard = 0
regCard = 0
timeLoggedIn = 0
loginBalance = 0
balanceLeft = 0

# Flags
hasCard = False
isLoginPatching = False
isLogoutPatching = False



async def attempt_login(url):
    global isLoginPatching, timeLoggedIn, loginBalance
    isLoginPatching = True
    print("LOGGING IN")
    response = requests.patch(url, json={'is_using': True})    
    print(response.json())
    if response.status_code == 200:
        print("Valid card scanned")
        timeLoggedIn = time.time()
        loginBalance = response.json()['balance']
        actuate_login()
 
    else:
        print("Invalid/Unregistered card scanned")
    isLoginPatching = False


def actuate_login():
    global balanceLeft, regCard, unlockitSocket
    balanceLeft = loginBalance
    regCard = currCard
    if balanceLeft > 0:
        unlockitSocket.on()

async def attempt_logout(url):
    global isLogoutPatching
    isLogoutPatching = True
    print("LOGGING OUT")
    response = requests.patch(url, json={'balance': int(balanceLeft), 'is_using': False})
    print(response.json())
    actuate_logout()
    isLogoutPatching = False
    
def actuate_logout():
    global regCard, loginBalance, balanceLeft
    regCard = 0
    loginBalance = 0
    balanceLeft = 0
    unlockitSocket.off()
    


async def main():
    global currCard, regCard, hasCard, isLoginPatching, isLogoutPatching, timeLoggedIn, balanceLeft
    while True:
        try:
            with Timeout(1):
                currCard = 0
                print("reading card...")
                currCard, cardText = reader.read()
                print("Card Found: {}".format(currCard))
                time.sleep(1)
        except:
            if currCard == 0:
                print("No Card")
        finally:
            GPIO.cleanup()
        
        # handle login if new card found
        if regCard == 0 and currCard != regCard:
            if not isLoginPatching:
                asyncio.create_task(
                    attempt_login('https://unlockitsocketapp.herokuapp.com/api/simple/students/{}/'.format(currCard))
                )
                
        # handle logout if registered card is no more
        elif regCard > 0 and currCard != regCard:
            if not isLogoutPatching:
                asyncio.create_task(
                    attempt_logout('https://unlockitsocketapp.herokuapp.com/api/simple/students/{}/'.format(regCard))
                )
                
        #important: await allows login and logout threads to run        
        await asyncio.sleep(0.1)
        
        # handle balance calculations
        if regCard > 0:
            balanceLeft = loginBalance - (time.time() - timeLoggedIn)
            balanceLeft = balanceLeft if balanceLeft > 0 else 0
            print("Balance left: {}".format(balanceLeft))
            if balanceLeft <= 0:
                print("YOUR TIME IS UP, PINHEAD!")
                logoutTask = asyncio.create_task(
                    attempt_logout('https://unlockitsocketapp.herokuapp.com/api/simple/students/{}/'.format(regCard))
                )
            
            
        
        
        
        

asyncio.run(main())

