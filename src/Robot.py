
import pygame
import random
import logging as log
from src.consts import *
class Robot:
    colors_map = {'r':'Red', 'w': 'White', 'b':'Blue', 'gr':'Green', 'y':'Yellow', 'g':'Gray'}
    def __init__(self, pos, index, color, mail=0, count_mail=0, battery=MAXIMUM_ROBOT_BATTERY, allowed_step_per_turn=1):
        self.pos = pos
        self.pos.robot = self
        self.index = index
        self.color = color
        self.mail = mail
        self.count_mail = count_mail
        self.battery = battery
        self.allowed_step_per_turn = allowed_step_per_turn
        self.set_image()
        self.set_number_image()

    def move_up(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.front:
                if self.pos.front.color != 'r' and not self.pos.front.robot and (self.pos.front.color != 'y' or self.pos.front.target == self.mail):
                    self.pos.robot = None 
                    self.pos = self.pos.front
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(f'{self.colors_map[self.color]} robot {self.index} go up to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    return True
        return False
    
    def move_down(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.back:
                if self.pos.back.color != 'r' and not self.pos.back.robot and (self.pos.back.color != 'y' or self.pos.back.target == self.mail):
                    self.pos.robot = None
                    self.pos = self.pos.back
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(f'{self.colors_map[self.color]} robot {self.index} go down to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    return True
        return False

    def move_right(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.right:
                if self.pos.right.color != 'r' and not self.pos.right.robot and (self.pos.right.color != 'y' or self.pos.right.target == self.mail):
                    self.pos.robot = None
                    self.pos = self.pos.right
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(f'{self.colors_map[self.color]} robot {self.index} go left to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    return True
        return False

    def move_left(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.left:
                if self.pos.left.color != 'r' and not self.pos.left.robot and (self.pos.left.color != 'y' or self.pos.left.target == self.mail):    
                    self.pos.robot = None
                    self.pos = self.pos.left
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1 
                    log.info(f'{self.colors_map[self.color]} robot {self.index} go right to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    return True
        return False   

    def pick_up(self):
        if self.mail == 0 and self.pos.color == 'gr':
            self.mail = random.choice(range(1,10))
            log.info(f'{self.colors_map[self.color]} robot {self.index} pick up mail {self.mail}')
            return True
        return False

    def drop_off(self):
        if self.mail != 0 and self.pos.color == 'y':
            deliveried_mail = self.mail
            self.mail = 0 
            self.count_mail += 1
            log.info(f'{self.colors_map[self.color]} robot {self.index} drop off mail {deliveried_mail}')
            return deliveried_mail
        return False

    def charge(self):
        self.battery += BATERRY_UP_PER_STEP
        if self.battery > MAXIMUM_ROBOT_BATTERY:
            self.battery = MAXIMUM_ROBOT_BATTERY
    
    @property
    def is_charged(self):
        return self.pos.color == 'b'

    def set_image(self):
        if self.color == 'b':
            self.img = pygame.image.load('images/blue_robot.png')
        if self.color == 'r':        
            self.img = pygame.image.load('images/red_robot.png')
        if self.color == 'y':        
            self.img = pygame.image.load('images/yellow_robot.png')
        if self.color == 'gr':        
            self.img = pygame.image.load('images/green_robot.png')
        if self.color == 'w':        
            self.img = pygame.image.load('images/white_robot.png')
        self.img = pygame.transform.scale(self.img, DEFAULT_IMAGE_SIZE)
    
    def set_number_image(self):
        robot_number_font = pygame.font.SysFont(None, 16)
        self.number_img = robot_number_font.render(str(self.index), True, (0,0,0))

    def set_destination(self, board):
        if self.battery <= 22:
            self.dest = min(board.blue_cells, key=lambda blue_cell : len(board.a_star_search(self.pos, blue_cell)))
        else:
            if self.mail:
                for yellow_cell in board.yellow_cells:
                    if yellow_cell.target == self.mail: 
                        self.dest = yellow_cell
                        break
            else:
                self.dest = min(board.green_cells, key=lambda green_cell : len(board.a_star_search(self.pos, green_cell)))
    
