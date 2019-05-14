from gpiozero import LED

unlockit_socket = LED(14)

while True:
    unlockit_socket.on()
