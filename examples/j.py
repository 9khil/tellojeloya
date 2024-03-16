import keyboard
from djitellopy import Tello

tello = Tello()

tello.connect()
tello.takeoff()

while True: 
    if keyboard.read_key() == "space":
        tello.move_up(10);    
    if keyboard.read_key() == "l":
        tello.land()
    
# tello.move_left(100)
# tello.rotate_clockwise(90)
# tello.move_forward(100)

# 
