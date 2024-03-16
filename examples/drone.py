from djitellopy import Tello
import asyncio
import websockets
import threading
import pyautogui
import cv2
import pygame
import numpy as np
import json
import time
from multiprocessing import Process

from pygame.event import Event

# Speed of the drone
S = 40

# Frames per second of the pygame window display
# A low number also results in input lag, as input information is processed once per frame.
FPS = 120

# Team Mega
DEBUG = False
JUMPSPEED = 100
FORWARD_SPEED = 40
GRAVITY = -40
MAX_JUMP_TIME = 1000  # milliseconds


# Use a dictionary to track keys and the time they were pressed
key_press_times = {}


class FrontEnd(object):
    """Maintains the Tello display and moves it through the keyboard keys.
    Press escape key to quit.
    The controls are:
        - T: Takeoff
        - L: Land
        - Arrow keys: Forward, backward, left and right.
        - A and D: Counter clockwise and clockwise rotations (yaw)
        - W and S: Up and down.

        Team Mega:
        - J: jump
    """

    TIMES_JUMPED = 0
    HEIGHT = "grounded"

    def __init__(self):
        # Init pygame
        pygame.init()

        # Creat pygame window
        pygame.display.set_caption("Flappydrone #1")
        self.screen = pygame.display.set_mode([960, 720])

        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10

        self.send_rc_control = False

        # create update timer
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000 // FPS)

    def run(self):

        websocket_thread = threading.Thread(target=self.start_websocket_thread)
        websocket_thread.start()

        self.tello.connect()
        self.tello.set_speed(self.speed)

        # In case streaming is on. This happens when we quit this program without the escape key.
        self.tello.streamoff()
        self.tello.streamon()

        frame_read = self.tello.get_frame_read()

        should_stop = False
        while not should_stop:

            # print(self.tof())
            # if(HEIGHT != str(self.tof())):
            # self.send_message(str(self.tof()))

            if self.TIMES_JUMPED > 0:
                self.for_back_velocity = FORWARD_SPEED

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.update()
                elif event.type == pygame.QUIT:
                    should_stop = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        should_stop = True
                    elif event.key not in key_press_times:
                        self.keydown(event.key)
                        key_press_times[event.key] = pygame.time.get_ticks()
                elif event.type == pygame.KEYUP:
                    self.keyup(event.key)

            keys = pygame.key.get_pressed()
            for key, press_time in list(key_press_times.items()):
                if (
                    not keys[key]
                    or pygame.time.get_ticks() - press_time > MAX_JUMP_TIME
                ):
                    print(f"Action for key {key} stopped")
                    del key_press_times[key]
                    self.abortJump()

            if frame_read.stopped:
                break

            self.screen.fill([0, 0, 0])

            frame = frame_read.frame
            # battery %
            text = "Battery: {}%".format(self.tello.get_battery())
            textD = "Height: {} cm".format(self.tof())
            cv2.putText(
                frame, text, (5, 720 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
            )
            cv2.putText(
                frame, textD, (5, 680 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
            )
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = np.flipud(frame)

            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            time.sleep(1 / FPS)

        # Call it always before finishing. To deallocate resources.
        self.tello.end()

    # async def send_message(self):
    #     print("SEND MESSAGE")
    #     print("SEND MESSAGE")
    #     print("SEND MESSAGE")
    #     print("SEND MESSAGE")
    #     uri = "ws://192.168.0.100:3000?type=drones&clientId=0"
    #     async with websockets.connect(uri) as websocket:
    #         while True:
    #             try:
    #                 print("prøver å sende banan")
    #                 await websocket.send("banan")
    #             except Exception as e:
    #                 print(f"Connection lost?: {e}")

    async def connectToGameServer(self):
        uri = "ws://192.168.0.100:3000?type=drones&clientId=0"  # Replace this with the actual WebSocket server address
        async with websockets.connect(uri) as websocket:
            send_task = asyncio.create_task(self.send_messages(websocket))
            recv_task = asyncio.create_task(self.receive_messages(websocket))

        # Wait for both tasks to complete
        await asyncio.gather(send_task, recv_task)

    async def send_messages(self, websocket):
        prev_height = None
        while True:
            if prev_height != self.HEIGHT:
                await websocket.send(self.HEIGHT)
                prev_height = self.HEIGHT
            elif not self.message_queue.empty():
                message_to_send = self.message_queue.get()
                await websocket.send(message_to_send)

    async def receive_messages(self, websocket):
        while True:
            message_received = await websocket.recv()
            if isinstance(message_received, str):
                print("GOT STRING")
                parsed_data = json.loads(message_received)
                if parsed_data["action"] == "jump":
                    print("received message:", message_received)
                    self.jump(parsed_data["duration"])

    def jump(self, duration):
        self.TIMES_JUMPED = self.TIMES_JUMPED + 1
        self.up_down_velocity = JUMPSPEED
        time.sleep(duration / 1000)
        self.abortJump()

    def abortJump(self):
        self.up_down_velocity = GRAVITY

    def tof(self):
        toff = self.tello.get_distance_tof()
        if toff < 30:
            return "dead"
        elif toff == 6553:
            return "grounded"
        else:
            return self.tello.get_distance_tof()

    def keydown(self, key):
        """Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw counter clockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw clockwise velocity
            self.yaw_velocity = S
        elif key == pygame.K_j:  # JUMP
            self.jump()

    def keyup(self, key):
        """Update velocities based on key released
        Arguments:
            key: pygame key
        """
        if (
            key == pygame.K_UP or key == pygame.K_DOWN
        ):  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif (
            key == pygame.K_LEFT or key == pygame.K_RIGHT
        ):  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            not self.tello.land()
            self.send_rc_control = False
        elif key == pygame.K_j:  # JUMP
            if key in key_press_times:
                del key_press_times[key]
            self.abortJump()

    def update(self):
        """Update routine. Send velocities to Tello."""
        if self.send_rc_control:
            self.tello.send_rc_control(
                self.left_right_velocity,
                self.for_back_velocity,
                self.up_down_velocity,
                self.yaw_velocity,
            )


def main():
    frontend = FrontEnd()

    # run frontend

    frontend.run()

    # Create an event loop
    loop = asyncio.get_event_loop()

    # Run the frontend and the WebSocket connection
    loop.run_until_complete(frontend.connectToGameServer())


if __name__ == "__main__":
    main()
