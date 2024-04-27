from __future__ import annotations
import random
import logging as log
from typing import Any

import pygame
import numpy as np

from Game import Cell
from Game import Clock
from Game import Mail
from Game.consts import *


class Robot(pygame.sprite.Sprite):

    colors_map = {
        'r': 'Red',
        'b': 'Blue',
        'g': 'Green',
        'y': 'Yellow',
        'o': 'Orange'
    }

    def __init__(self,
                 pos: Cell.Cell,
                 index: int,
                 color: str,
                 sprites_group: pygame.sprite.Group,
                 clock: Clock.Clock,
                 mail: Mail.Mail | None = None,
                 count_mail: int = 0,
                 battery: int = MAXIMUM_ROBOT_BATTERY,
                 allowed_step_per_turn: int = 1,
                 render_mode = None) -> None:
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
        self.render_mode = render_mode
        if self.render_mode == 'human':
            self.__set_image()
            self.__set_number_image()

    def __set_image(self) -> None:
        if self.color == 'b':
            self.image = pygame.image.load('images/blue_robot.png')
        if self.color == 'r':
            self.image = pygame.image.load('images/red_robot.png')
        if self.color == 'y':
            self.image = pygame.image.load('images/yellow_robot.png')
        if self.color == 'g':
            self.image = pygame.image.load('images/green_robot.png')
        if self.color == 'o':
            self.image = pygame.image.load('images/orange_robot.png')
        self.image = pygame.transform.scale(self.image, CELL_SIZE)

    def __set_number_image(self) -> None:
        robot_number_font = pygame.font.SysFont(None, 16)
        number_img = robot_number_font.render(str(self.index), True, (0, 0, 0))
        self.image.blit(number_img,
                        (0.5 * CELL_SIZE[0] - number_img.get_width() / 2,
                         0.7 * CELL_SIZE[1] - number_img.get_height() / 2))

    @property
    def state(self) -> dict[str, Any]:
        state = {
            'color': self.color,
            'index': self.index,
            'pos': (self.pos.x, self.pos.y),
            'mail': self.mail.mail_number if self.mail else 0,
            'count_mail': self.count_mail,
            'battery': self.battery
        }
        return state

    @property
    def observation(self):
        mail = self.mail.mail_number if self.mail else 0
        return (self.pos.x*9 + self.pos.y)*10+mail
    
    @property
    def is_charged(self) -> bool:
        return self.pos.color == 'b'

    @property
    def rect(self) -> pygame.Rect:
        rect = self.image.get_rect()
        rect.topleft = ((self.pos.x + 1) * CELL_SIZE[0],
                        (self.pos.y + 1) * CELL_SIZE[1])
        return rect

    def move_up(self) -> bool:
        if self.allowed_step_per_turn and self.battery:
            if self.pos.front:
                if self.pos.front.color != 'r' and not self.pos.front.robot and (
                        self.pos.front.color != 'y' or
                    (self.mail
                     and self.pos.front.target == self.mail.mail_number)) and (
                         self.pos.front.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail(self.sprites_group, self.render_mode)
                    self.pos = self.pos.front
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go up to position ({self.pos.x},{self.pos.y})'
                    )
                    if self.mail:
                        self.mail.pos = self.pos
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False

    def move_down(self) -> bool:
        if self.allowed_step_per_turn and self.battery:
            if self.pos.back:
                if self.pos.back.color != 'r' and not self.pos.back.robot and (
                        self.pos.back.color != 'y' or
                    (self.mail
                     and self.pos.back.target == self.mail.mail_number)) and (
                         self.pos.back.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail(self.sprites_group, self.render_mode)
                    self.pos = self.pos.back
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go down to position ({self.pos.x},{self.pos.y})'
                    )
                    if self.mail:
                        self.mail.pos = self.pos
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False

    def move_right(self) -> bool:
        if self.allowed_step_per_turn and self.battery:
            if self.pos.right:
                if self.pos.right.color != 'r' and not self.pos.right.robot and (
                        self.pos.right.color != 'y' or
                    (self.mail
                     and self.pos.right.target == self.mail.mail_number)) and (
                         self.pos.right.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail(self.sprites_group, self.render_mode)
                    self.pos = self.pos.right
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go left to position ({self.pos.x},{self.pos.y})'
                    )
                    if self.mail:
                        self.mail.pos = self.pos
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False

    def move_left(self) -> bool:
        if self.allowed_step_per_turn and self.battery:
            if self.pos.left:
                if self.pos.left.color != 'r' and not self.pos.left.robot and (
                        self.pos.left.color != 'y' or
                    (self.mail
                     and self.pos.left.target == self.mail.mail_number)) and (
                         self.pos.left.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail(self.sprites_group, self.render_mode)
                    self.pos = self.pos.left
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go right to position ({self.pos.x},{self.pos.y})'
                    )
                    if self.mail:
                        self.mail.pos = self.pos
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False

    def pick_up(self) -> bool:
        if not self.mail and self.pos.color == 'gr':
            self.mail = self.pos.mail
            log.info(
                f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} pick up mail {self.mail.mail_number}'
            )
            return True
        return False

    def drop_off(self) -> bool | Mail.Mail:
        if self.mail and self.pos.color == 'y':
            deliveried_mail = self.mail
            self.mail.kill()
            self.mail = None
            self.count_mail += 1
            log.info(
                f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} drop off mail {deliveried_mail.mail_number}'
            )
            return deliveried_mail
        return False

    def charge(self) -> None:
        self.battery += BATERRY_UP_PER_STEP
        if self.battery > MAXIMUM_ROBOT_BATTERY:
            self.battery = MAXIMUM_ROBOT_BATTERY
    
    def reset(self, pos: Cell.Cell) -> None:
        self.pos = pos
        self.pos.robot = self
        self.mail = None
        self.count_mail = 0
        self.battery = MAXIMUM_ROBOT_BATTERY
        self.allowed_step_per_turn = 1

    def step(self, action: int) -> bool:
        if action == 0:
            return False
        if action == 1:
            return self.move_up()
        if action == 2:
            return self.move_down()
        if action == 3:
            return self.move_left()
        if action == 4:
            return self.move_right()
        return False
    
    def reward(self, action):
        reward = -0.1
        if action == 1 and self.mail is not None and self.pos.front and self.pos.front.target == self.mail.mail_number:
            reward = 20
        if action == 2 and self.mail is not None and self.pos.back and self.pos.back.target == self.mail.mail_number:
            reward = 20
        if action == 3 and self.mail is not None and self.pos.left and self.pos.left.target == self.mail.mail_number:
            reward = 20
        if action == 4 and self.mail is not None and self.pos.right and self.pos.right.target == self.mail.mail_number:
            reward = 20

        if action == 1 and self.mail is None and self.pos.front and self.pos.front.color == 'gr':
            reward = 20
        if action == 2 and self.mail is None and self.pos.back and self.pos.back.color == 'gr':
            reward = 20
        if action == 3 and self.mail is None and self.pos.left and self.pos.left.color == 'gr':
            reward = 20
        if action == 4 and self.mail is None and self.pos.right and self.pos.right.color == 'gr':
            reward = 20
        return reward
        
    def is_legal_moves(self, action: int) -> bool:
        if action == 0:
            return True
        if action == 1:
            if self.pos.front:
                if self.pos.front.color != 'r' and self.pos.front.robot is None and (
                        self.pos.front.color != 'y' or
                    (self.mail
                     and self.pos.front.target == self.mail.mail_number)) and (
                         self.pos.front.color != 'gr' or self.mail is None):
                    return True
            
        if action == 2:
            if self.pos.back:
                if self.pos.back.color != 'r' and self.pos.back.robot is None and (
                        self.pos.back.color != 'y' or
                    (self.mail
                     and self.pos.back.target == self.mail.mail_number)) and (
                         self.pos.back.color != 'gr' or self.mail is None):
                    return True
                
        if action == 3:
            if self.pos.left:
                if self.pos.left.color != 'r' and self.pos.left.robot is None and (
                        self.pos.left.color != 'y' or
                    (self.mail
                     and self.pos.left.target == self.mail.mail_number)) and (
                         self.pos.left.color != 'gr' or self.mail is None):
                    return True
                
        if action == 4:
            if self.pos.right:
                if self.pos.right.color != 'r' and self.pos.right.robot is None and (
                        self.pos.right.color != 'y' or
                    (self.mail
                     and self.pos.right.target == self.mail.mail_number)) and (
                         self.pos.right.color != 'gr' or self.mail is None):
                    return True
                
        return False