from machine import Pin, I2C
import sh1106
from time import ticks_ms, sleep
from button_repeat import KeyRepeat
import random

# Initialize buttons
button_L = KeyRepeat(29, repeat_delay = 100)
button_R = KeyRepeat(26, repeat_delay = 100)
button_rotate = KeyRepeat(27)


game_speed = 100

# Initialize I2C and display
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
display = sh1106.SH1106_I2C(128, 64, i2c, Pin(16), 0x3c, rotate=90)
display.sleep(False)
display.fill(0)

# Tetromino shapes
shapes = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    #[[1, 0, 1], [1, 1, 1]],  # U
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# Game grid
grid = [[0 for _ in range(10)] for _ in range(20)]
piece_queue = [random.choice(shapes) for _ in range(4)]
# Current piece
current_piece = None
current_x = 0
current_y = 0
scale = 3

def draw_bigger_pixels(x, y, c):
    for i in range(scale):
        for j in range(scale):
            display.pixel(x * scale + i, y * scale + j, c)


def new_piece():
    global current_piece, current_x, current_y
    current_piece = piece_queue.pop(0)
    piece_queue.append(random.choice(shapes))
    current_x = 5
    current_y = 0

def draw_piece():
    for y, row in enumerate(current_piece):
        for x, cell in enumerate(row):
            if cell:
                draw_bigger_pixels(current_x + x, current_y + y, 1)

def draw_queue():
    # Define the starting position for the queue display
    queue_x = scale * 10 + 5  # Start a few pixels to the right of the grid
    queue_y_start = 5  # Start a few pixels from the top

    for i, piece in enumerate(piece_queue):
        # Draw each piece in the queue
        for y, row in enumerate(piece):
            for x, cell in enumerate(row):
                if cell:
                    # Draw each cell of the piece
                    for dx in range(scale):
                        for dy in range(scale):
                            display.pixel(queue_x + x * scale + dx, queue_y_start + i * 4 * scale + y * scale + dy, 1)

def draw_grid():
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x]:
                draw_bigger_pixels(x, y, 1)

def check_collision():
    for y, row in enumerate(current_piece):
        for x, cell in enumerate(row):
            if cell:
                if (current_x + x < 0 or
                    current_x + x >= 10 or
                    current_y + y >= 20 or
                    (current_y + y >= 0 and grid[current_y + y][current_x + x])):
                    return True
    return False

def merge_piece():
    for y, row in enumerate(current_piece):
        for x, cell in enumerate(row):
            if cell and current_y + y >= 0:
                grid[current_y + y][current_x + x] = cell

def clear_lines():
    global grid
    new_grid = [row for row in grid if any(cell == 0 for cell in row)]
    lines_cleared = len(grid) - len(new_grid)
    new_lines = [[0 for _ in range(10)] for _ in range(lines_cleared)]
    grid = new_lines + new_grid

def rotate_piece():
    global current_piece
    current_piece = [list(row) for row in zip(*current_piece[::-1])]
    if check_collision():
        current_piece = [list(row) for row in zip(*current_piece)][::-1]

def restart_game():
    display.fill(0)
    display.line(scale*10, 1, scale * 10, scale*20, 1)
    display.line(1, scale*20, scale * 10, scale*20, 1)
    draw_queue()
    display.show()


restart_game()
new_piece()
draw_queue()
start_millis = ticks_ms()
while True:
    #print(button_rotate.is_clicked, button_rotate.current_state)
    
    display.fill_rect(0,0, scale * 10,scale * 20, 0)
    
    # display.text(str(ticks_ms()), 0, 50, 1)

    if button_L.update():
        current_x -= 1
    if check_collision():
        current_x += 1

    if button_R.update():
        current_x += 1
        if check_collision():
            current_x -= 1

    if button_rotate.update():
        rotate_piece()
        
    current_millis = ticks_ms()
    if current_millis - start_millis >= game_speed:
        current_y += 1
        start_millis = current_millis
        
    if check_collision():
        current_y -= 1
        merge_piece()
        clear_lines()
        new_piece()
        
        display.fill_rect(scale * 10+1, 0, 64, scale * 20, 0)
        draw_queue()
        
        if check_collision():  # Game over
            display.fill(0)
            display.text("GG", 10, 10, 1)
            display.show()
            sleep(1)
            restart_game()
            grid = [[0 for _ in range(10)] for _ in range(20)]

    draw_grid()
    draw_piece()
    display.show()
