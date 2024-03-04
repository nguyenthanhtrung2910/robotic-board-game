from Game.consts import *
class Clock:
    def __init__(self) -> None:
        self.now = 0
    
    def up(self):
        self.now += DELTA_T

    def reset(self):
        self.now = 0