
import pygame
import random
import logging as log
from src.consts import *
from src.Mail import Mail
from src.Board import heuristic
class Robot(pygame.sprite.Sprite):
    colors_map = {'r':'Red', 'w': 'White', 'b':'Blue', 'gr':'Green', 'y':'Yellow', 'g':'Gray', 'o':'Orange'}
    def __init__(self, pos, index, color, sprites_group, clock, mail=None, count_mail=0, battery=MAXIMUM_ROBOT_BATTERY, allowed_step_per_turn=1):
        super().__init__()
        self.pos = pos
        self.pos.robot = self
        self.index = index
        self.color = color
        self.sprites_group = sprites_group
        self.clock = clock
        self.mail = mail
        self.count_mail = count_mail
        self.battery = battery
        self.allowed_step_per_turn = allowed_step_per_turn
        self.set_image()
        self.set_number_image()

    def move_up(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.front:
                if self.pos.front.color != 'r' and not self.pos.front.robot and (self.pos.front.color != 'y' or (self.mail and self.pos.front.target == self.mail.mail_number)):
                    self.pos.robot = None 
                    self.pos = self.pos.front
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    # log.info(f'{self.colors_map[self.color]} robot {self.index} go up to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False
    
    def move_down(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.back:
                if self.pos.back.color != 'r' and not self.pos.back.robot and (self.pos.back.color != 'y' or (self.mail and self.pos.back.target == self.mail.mail_number)):
                    self.pos.robot = None
                    self.pos = self.pos.back
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    # log.info(f'{self.colors_map[self.color]} robot {self.index} go down to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False

    def move_right(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.right:
                if self.pos.right.color != 'r' and not self.pos.right.robot and (self.pos.right.color != 'y' or (self.mail and self.pos.right.target == self.mail.mail_number)):
                    self.pos.robot = None
                    self.pos = self.pos.right
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    # log.info(f'{self.colors_map[self.color]} robot {self.index} go left to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False

    def move_left(self):
        if self.allowed_step_per_turn and self.battery:
            if self.pos.left:
                if self.pos.left.color != 'r' and not self.pos.left.robot and (self.pos.left.color != 'y' or (self.mail and self.pos.left.target == self.mail.mail_number)):    
                    self.pos.robot = None
                    self.pos = self.pos.left
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1 
                    # log.info(f'{self.colors_map[self.color]} robot {self.index} go right to position ({self.pos.x},{self.pos.y})')
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False   

    def pick_up(self):
        if not self.mail and self.pos.color == 'gr':
            self.mail = Mail(random.choice(range(1,10)), self)
            self.sprites_group.add(self.mail)
            # log.info(f'{self.colors_map[self.color]} robot {self.index} pick up mail {self.mail.mail_number}')
            return True
        return False

    def drop_off(self):
        if self.mail and self.pos.color == 'y':
            deliveried_mail = self.mail
            self.mail.kill() 
            self.mail = None
            self.count_mail += 1
            # log.info(f'{self.colors_map[self.color]} robot {self.index} drop off mail {deliveried_mail.mail_number}')
            return deliveried_mail
        return False

    def charge(self):
        self.battery += BATERRY_UP_PER_STEP
        if self.battery > MAXIMUM_ROBOT_BATTERY:
            self.battery = MAXIMUM_ROBOT_BATTERY
    
    @property
    def is_charged(self):
        return self.pos.color == 'b'
    
    @property
    def rect(self):
        rect = self.image.get_rect()
        rect.topleft = ((self.pos.x+1)*DEFAULT_IMAGE_SIZE[0], (self.pos.y+1)*DEFAULT_IMAGE_SIZE[1])
        return rect

    def set_image(self):
        if self.color == 'b':
            self.image = pygame.image.load('images/blue_robot.png')
        if self.color == 'r':        
            self.image = pygame.image.load('images/red_robot.png')
        if self.color == 'y':        
            self.image = pygame.image.load('images/yellow_robot.png')
        if self.color == 'gr':        
            self.image = pygame.image.load('images/green_robot.png')
        if self.color == 'w':        
            self.image = pygame.image.load('images/white_robot.png')
        if self.color == 'o':        
            self.image = pygame.image.load('images/orange_robot.png')    
        self.image = pygame.transform.scale(self.image, DEFAULT_IMAGE_SIZE)

    def set_number_image(self):
        robot_number_font = pygame.font.SysFont(None, 16)
        number_img = robot_number_font.render(str(self.index), True, (0,0,0))
        self.image.blit(number_img, (0.5*DEFAULT_IMAGE_SIZE[0] - number_img.get_width()/2, 
                                     0.7*DEFAULT_IMAGE_SIZE[1] - number_img.get_height()/2))

    def set_destination(self, board, blocked):
        if self.battery <= 30:
            min_appoaching_robot = min([cell.number_appoaching_robots for cell in board.blue_cells if cell not in blocked])
            self.dest = min([cell for cell in board.blue_cells if cell.number_appoaching_robots == min_appoaching_robot and cell not in blocked], 
                             key=lambda blue_cell :heuristic(self.pos, blue_cell))
        else:
            if self.mail:
                for yellow_cell in board.yellow_cells:
                    if yellow_cell.target == self.mail.mail_number: 
                        self.dest = yellow_cell
                        break
            else:
                min_appoaching_robot = min([cell.number_appoaching_robots for cell in board.green_cells if cell not in blocked])
                self.dest = min([cell for cell in board.green_cells if cell.number_appoaching_robots == min_appoaching_robot and cell not in blocked], 
                                 key=lambda green_cell : heuristic(self.pos, green_cell))
                
        self.dest.number_appoaching_robots += 1
