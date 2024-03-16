import pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 640, 480
FPS = 60

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Use a dictionary to track keys and the time they were pressed
key_press_times = {}

# Start the game loop
running = True
while running:
    dt = pygame.time.Clock().tick(FPS)  # Amount of seconds between each loop
    screen.fill((0, 0, 0))  # Fill the screen with black

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key not in key_press_times:
                print(f"Key {event.key} pressed")
                key_press_times[event.key] = pygame.time.get_ticks()
        elif event.type == pygame.KEYUP:
            if event.key in key_press_times:
                del key_press_times[event.key]

    keys = pygame.key.get_pressed()
    for key, press_time in list(key_press_times.items()):
        if not keys[key] or pygame.time.get_ticks() - press_time > 500:
            print(f"Action for key {key} stopped")
            del key_press_times[key]

    pygame.display.flip()  # Flip everything to the display

pygame.quit()
