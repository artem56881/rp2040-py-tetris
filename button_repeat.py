from machine import Pin
from time import ticks_ms
import utime

class KeyRepeat:
    def __init__(self, pin, repeat_delay=400, repeat_interval=100):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.repeat_delay = repeat_delay
        self.repeat_interval = repeat_interval
        self.last_state = 1
        self.first_press_time = 0
        self.last_repeat_time = 0
        self.repeating = False

    def update(self):
        now = ticks_ms()
        current_state = self.pin.value()

        if self.last_state == 1 and current_state == 0:  # just pressed
            self.first_press_time = now
            self.last_repeat_time = now
            self.repeating = False
            self.last_state = 0
            return True
        elif self.last_state == 0 and current_state == 0:  # held
            if not self.repeating and utime.ticks_diff(now, self.first_press_time) >= self.repeat_delay:
                self.repeating = True
                self.last_repeat_time = now
                return True
            elif self.repeating and utime.ticks_diff(now, self.last_repeat_time) >= self.repeat_interval:
                self.last_repeat_time = now
                return True
        elif current_state == 1:
            self.repeating = False
            self.last_state = 1
        return False
