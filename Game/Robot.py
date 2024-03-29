from __future__ import annotations
import random
import logging as log
from typing import Any
import pygame

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
                 allowed_step_per_turn: int = 1) -> None:
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
                     and self.pos.front.target == self.mail.mail_number)):
                    self.pos.robot = None
                    self.pos = self.pos.front
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go up to position ({self.pos.x},{self.pos.y})'
                    )
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
                     and self.pos.back.target == self.mail.mail_number)):
                    self.pos.robot = None
                    self.pos = self.pos.back
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go down to position ({self.pos.x},{self.pos.y})'
                    )
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
                     and self.pos.right.target == self.mail.mail_number)):
                    self.pos.robot = None
                    self.pos = self.pos.right
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go left to position ({self.pos.x},{self.pos.y})'
                    )
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
                     and self.pos.left.target == self.mail.mail_number)):
                    self.pos.robot = None
                    self.pos = self.pos.left
                    self.pos.robot = self
                    self.allowed_step_per_turn -= 1
                    self.battery -= 1
                    log.info(
                        f'At t={self.clock.now:04} {self.colors_map[self.color]:>5} robot {self.index} go right to position ({self.pos.x},{self.pos.y})'
                    )
                    self.pick_up()
                    self.drop_off()
                    self.clock.up()
                    return True
        return False

    def pick_up(self) -> bool:
        if not self.mail and self.pos.color == 'gr':
            self.mail = Mail.Mail(random.choice(range(1, 10)), self)
            self.sprites_group.add(self.mail)
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

    def move(self, action: str) -> bool:
        if action == 's':
            return False
        if action == 'u':
            return self.move_up()
        if action == 'd':
            return self.move_down()
        if action == 'l':
            return self.move_left()
        if action == 'r':
            return self.move_right()
        return False