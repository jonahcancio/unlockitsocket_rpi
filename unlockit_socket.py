import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from gpiozero import LED
import I2C_LCD_driver

import signal
import time
import datetime

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
mylcd = I2C_LCD_driver.lcd()

# card values
currentCard = 0
registeredCard = 0
timeLoggedIn = 0
loginBalance = 0
balanceLeft = 0
studentName = ""
studentNumber = 0
decrement = 0


def attempt_login(url):
    global timeLoggedIn, loginBalance, studentName, studentNumber
    print("attempting login...")
    response = requests.patch(url, json={'is_using': True})    
    print(response.json())
    if response.status_code == 200:
        print("Valid card found")
        timeLoggedIn = time.time()
        loginBalance = response.json()['balance']
        studentName = response.json()['name']
        actuate_login()
    else:
        print("LOGIN FAILED: invalid card")
        mylcd.lcd_display_string("Unregistered Card!", 1)


def actuate_login():
    global balanceLeft, registeredCard, decrement, unlockitSocket
    balanceLeft = loginBalance
    decrement = 0
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Hello {}!".format(studentName), 1)
    if balanceLeft > 0:
        registeredCard = currentCard
        unlockitSocket.on()
    else:
        mylcd.lcd_display_string("You have no load :(", 2)

def attempt_logout(url):
    global decrement
    print("attempting logout...")
    actuate_logout()
    print("decrement: {}".format(decrement))
    response = requests.patch(url, json={'decrement': int(decrement), 'is_using': False})
    print(response.json())
    if response.status_code == 200:
        print("LOGOUT SUCCESS")
    else:
         print("LOGOUT FAILED")
    
def actuate_logout():
    global registeredCard, loginBalance, balanceLeft
    registeredCard = 0
    loginBalance = 0
    unlockitSocket.off()
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Bye {}!".format(studentName), 1)
    print_lcd_balance(balanceLeft)

def print_lcd_balance(seconds):
    balanceOutput = datetime.timedelta(seconds=seconds)
    mylcd.lcd_display_string("Balance: {}".format(balanceOutput), 2)

def main():
    global currentCard, registeredCard, timeLoggedIn, balanceLeft, decrement
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
                mylcd.lcd_clear()
                mylcd.lcd_display_string("No Card", 1)
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
            decrement = time.time() - timeLoggedIn
            balanceLeft = loginBalance - decrement
            balanceLeft = balanceLeft if balanceLeft > 0 else 0
            print("Balance left: {}".format(balanceLeft))
            print_lcd_balance(balanceLeft)
            if balanceLeft <= 0:
                print("YOUR TIME IS UP, PINHEAD!")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("YOUR TIME IS UP!", 2)
                attempt_logout('https://unlockitsocketapp.herokuapp.com/api/simple/students/{}/'.format(registeredCard))

main()


