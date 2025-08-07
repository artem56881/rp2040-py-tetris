from machine import Pin, I2C, freq
import sh1106
from time import ticks_ms, sleep
from button_repeat import KeyRepeat
import random
freq(250_000_000)

button_L = KeyRepeat(27, repeat_delay = 100)
button_R = KeyRepeat(15, repeat_delay = 100)
button_D = Pin(26, Pin.IN, Pin.PULL_UP)
button_U = KeyRepeat(14)
button_S = KeyRepeat(28)
button_H = KeyRepeat(29)

DEBUG = False

game_speed = 1000
current_score = 0
high_score = 0
current_level = 1
total_lines_cleared = 0

default_game_speed = game_speed
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
display = sh1106.SH1106_I2C(128, 64, i2c, Pin(16), 0x3c, rotate=90)
display.sleep(False)
display.fill(0)

shapes = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

grid = [[0 for _ in range(10)] for _ in range(20)]
piece_queue = [random.choice(shapes) for _ in range(4)] # type: ignore
current_piece = None
holded_piece = None
can_hold = True
current_x = 0
current_y = 0
current_score = 0
shadow_y = 0
scale = 4

def save_score(score):
    try:
        with open('score.txt', 'w') as file:
            file.write(str(score))
    except Exception as e:
        print("Failed to save score:", e)
        
def load_high_score():
    try:
        with open('score.txt', 'r') as file:
            return int(file.read())
    except:
        return 0
    
high_score = load_high_score()

def draw_bigger_pixels(x, y, main_color, add_color = 1):
    display.fill_rect(x*scale, y*scale ,scale ,scale, main_color)
    display.fill_rect(x*scale + 1, y*scale + 1 ,scale - 2 ,scale - 2, add_color)

def new_piece():
    global current_piece, current_x, current_y
    current_piece = piece_queue.pop(0)
    piece_queue.append(random.choice(shapes))
    current_x = 4
    current_y = 0

def draw_piece(y_level, main_color, add_color):
    for y, row in enumerate(current_piece):
        for x, cell in enumerate(row):
            if cell:
                draw_bigger_pixels(current_x + x, y_level + y, main_color, add_color)

def find_shadow_y():
    y_level = 0
    while not(check_collision(y_level)):
        y_level += 1
    else:
        y_level -= 1
    return y_level


def draw_holded():
    for y, row in enumerate(holded_piece):
        for x, cell in enumerate(row):
            if cell:
                display.fill_rect(
                    scale * 10 + 5 + x * scale,
                    5 + 16 * scale + y * scale,
                    scale,
                    scale,
                    1
                )
                
                
def draw_queue():
    queue_x = scale * 10 + 5
    queue_y_start = 5

    for i, piece in enumerate(piece_queue):
        # Draw each piece in the queue
        for y, row in enumerate(piece):
            for x, cell in enumerate(row):
                if cell:
                    display.fill_rect(
                        queue_x + x * scale,
                        queue_y_start + i * 4 * scale + y * scale,
                        scale,
                        scale,
                        1
                    )


def draw_grid():
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x]:
                draw_bigger_pixels(x, y, 1)

def draw_score():
    x,y=0, scale*20+5
    display.fill_rect(x, y, 64, 8, 0)
    display.text(str(current_score), x, y, 1)


def draw_level():
    x,y=0, scale*20+13
    display.fill_rect(x, y, 64, 8, 0)
    display.text(str(current_level), x, y, 1)


def check_collision(y_level):
    for y, row in enumerate(current_piece):
        for x, cell in enumerate(row):
            if cell:
                if (current_x + x < 0 or
                    current_x + x >= len(grid[0]) or
                    y_level + y >= len(grid) or
                    (y_level + y >= 0 and grid[y_level + y][current_x + x])):
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
    return lines_cleared

def rotate_piece():
    global current_piece
    current_piece = [list(row) for row in zip(*current_piece[::-1])]
    if check_collision(current_y):
        current_piece = [list(row) for row in zip(*current_piece)][::-1]

def lock_piece_and_continue():
    global current_y, can_hold, current_score, total_lines_cleared, current_level, default_game_speed, game_speed, grid, high_score

    merge_piece()
    cleared_lines = clear_lines()
    total_lines_cleared += cleared_lines

    if total_lines_cleared >= current_level * 10:
        current_level += 1
        total_lines_cleared = 0
        default_game_speed //= 1.6
        game_speed = default_game_speed
    draw_level()

    if cleared_lines == 1:
        current_score += 40 * (current_level + 1)
    elif cleared_lines == 2:
        current_score += 100 * (current_level + 1)
    elif cleared_lines == 3:
        current_score += 300 * (current_level + 1)
    elif cleared_lines == 4:
        current_score += 1200 * (current_level + 1)

    new_piece()
    can_hold = True
    display.fill_rect(scale * 10 + 1, 0, 64, scale * 20 - 19, 0)
    draw_queue()

    if check_collision(current_y):
        draw_grid()
        display.fill_rect(0, 0, 64, 1, 0)
        for _ in range(128):
            display.scroll(0, 1)
            display.show()
        display.fill(0)
        if current_score > high_score:
            high_score = current_score
            save_score(high_score)
        display.text("GG", 17, 10, 1)
        display.text(f"S:{current_score}", 4, 19, 1)
        display.text(f"Hs:{high_score}", 4, 28, 1)
        display.show()

        while True:
            if button_U.update():
                break

        restart_game()
        grid = [[0 for _ in range(10)] for _ in range(20)]


def restart_game():
    global current_score
    global total_lines_cleared
    global current_level
    global game_speed
    global default_game_speed
    holded_piece = None
    display.fill(0)
    display.line(scale*10, 1, scale * 10, scale*20, 1)
    display.line(1, scale*20, scale * 10 + 5 * scale, scale*20, 1)
    display.line(scale * 10, scale*20-4*scale, scale * 10 + 5 * scale, scale*20-4*scale, 1)
    current_score = 0
    total_lines_cleared = 0
    current_level = 0
    game_speed = default_game_speed = 1000
    draw_queue()
    display.show()
    draw_level()


if button_D.value() == 0:
    DEBUG = True

if DEBUG:
    frame_counter = 0
    fps = 0
    fps_timer = ticks_ms()

restart_game()
new_piece()
draw_queue()
start_millis = ticks_ms()
while True:  
    display.fill_rect(0,0, scale * 10,scale * 20, 0)
    if button_L.update():
        current_x -= 1
        if check_collision(current_y):
            current_x += 1

    if button_R.update():
        current_x += 1
        if check_collision(current_y):
            current_x -= 1
            
    if button_D.value() == 0:
        game_speed = 1
    else:
        game_speed = default_game_speed
    
    if button_S.update():
        current_score += shadow_y - current_y
        current_y = shadow_y
        lock_piece_and_continue()

    
    if button_U.update():
        rotate_piece()
        
    if button_H.update():
        if can_hold:
            if holded_piece == None:
                holded_piece = current_piece
                new_piece()
            else:
                buff_piece = holded_piece
                holded_piece = current_piece
                current_piece = buff_piece
            display.fill_rect(scale * 10 + 1, scale*20-4*scale + 1, 5 * scale, 4 * scale - 1, 0)
            draw_holded()
            can_hold = False
            current_y = 0
        
    current_millis = ticks_ms()
    
    if current_millis - start_millis >= game_speed:
        current_y += 1
        current_score += 1
        start_millis = current_millis
        
    if check_collision(current_y):
        current_y -= 1
        lock_piece_and_continue()
            
    shadow_y = find_shadow_y()
    draw_grid()      
    draw_piece(shadow_y, 1, 0)
    draw_piece(current_y, 1, 1)
    draw_score()
    
    if DEBUG:
        frame_counter += 1
        now = ticks_ms()

        if now - fps_timer >= 1000:
            fps = frame_counter
            frame_counter = 0
            fps_timer = now
        display.fill_rect(0, 120, 28, 8, 0)
        display.text(str(fps), 0, 120, 1)
    display.show()
