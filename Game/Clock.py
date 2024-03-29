from Game.consts import *


class Clock:

    def __init__(self) -> None:
        self.now = 0

    def up(self) -> None:
        self.now += DELTA_T

    def reset(self) -> None:
        self.now = 0
