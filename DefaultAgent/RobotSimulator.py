import pygame
import random
from Game.consts import *
from DefaultAgent.BoardSimulator import BoardSimulator

class RobotSimulator:

    def __init__(self, pos, index, color, mail=0, count_mail=0, battery=MAXIMUM_ROBOT_BATTERY):
        self.pos = pos
        self.pos.robot = self
        self.index = index
        self.color = color
        self.mail = mail
        self.count_mail = count_mail
        self.battery = battery

    @property
    def is_charged(self):
        return self.pos.color == 'b'

    def pick_up(self):
        if not self.mail and self.pos.color == 'gr':
            self.mail = random.choice(range(1,10))
            return True
        return False

    def drop_off(self):
        if self.mail and self.pos.color == 'y':
            deliveried_mail = self.mail
            self.mail = 0
            self.count_mail += 1
            return deliveried_mail
        return False

    def charge(self):
        self.battery += BATERRY_UP_PER_STEP
        if self.battery > MAXIMUM_ROBOT_BATTERY:
            self.battery = MAXIMUM_ROBOT_BATTERY
    
    def set_destination(self, board, blocked=[]):
        if self.battery <= 30:
            self.dest = min([cell for cell in board.blue_cells if cell not in blocked], 
                                key=lambda blue_cell :BoardSimulator.heuristic(self.pos, blue_cell))
        else:
            if self.mail:
                for yellow_cell in board.yellow_cells:
                    if yellow_cell.target == self.mail: 
                        self.dest = yellow_cell
                        break
            else:
                self.dest = min([cell for cell in board.green_cells if cell not in blocked], 
                                    key=lambda green_cell : BoardSimulator.heuristic(self.pos, green_cell))
