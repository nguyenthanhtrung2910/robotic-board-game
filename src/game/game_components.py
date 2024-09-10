from __future__ import annotations
import random
import csv
import typing
import logging as log
import enum

import numpy as np
import pygame

from src.consts import *

class Action(enum.IntEnum):

    DO_NOTHING = 0
    GO_AHEAD = 1
    GO_BACK = 2
    TURN_LEFT = 3
    TURN_RIGHT = 4

class Cell:

    """
    A object representing a cell in game board.
    """

    def __init__(self,
                 y: int,
                 x: int,
                 color: str = 'w',
                 target: int = 0,
                 robot: Robot | None = None,
                 mail: Mail | None = None,
                 *,
                 front: 'Cell | None' = None,
                 back: 'Cell | None' = None,
                 left: 'Cell | None' = None,
                 right: 'Cell | None' = None) -> None:
    
        """
        :param x: the abscissa on the game board. The coordinate origin is at the top left point, positive direction from left to right.
        :type x: int
        :param y: the ordinate on the game board. The coordinate origin is at the top left point, positive direction from top to bottom.
        :type y: int
        :param color: the color of the cell. Possible colors are ``'w'`` - white, ``'b'`` - blue,  ``'r'`` - red, ``'y'`` - yellow, ``'gr'`` - green, ``'g'`` - gray.
        :type color: str
        :param target: the target number. Robot drops off in this cell only mail with this number. Equal 0 if in this cell can be drop off.  
        :type target: int
        :param robot: the located in this cell robot.
        :type robot: Robot or None
        :param mail: generated mail in this cell.
        :type mail: Mail or None
        :param front: the front cell of this cell.
        :type front: Cell or None
        :param back: the back cell of this cell.
        :type back: Cell or None
        :param left: the left cell of this cell.
        :type left: Cell or None
        :param right: the right cell of this cell.
        :type right: Cell or None
        """

        self.__x = x
        self.__y = y
        self.__color = color
        self.__target = target
        self.robot = robot
        self.mail = mail

        self.front = front
        self.back = back
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f'Cell({self.x}, {self.y})'

    #equal and hash dunder method for using a Cell as dictionary's key
    def __eq__(self, cell: object) -> bool:
        if isinstance(cell, Cell):
            return self.x == cell.x and self.y == cell.y
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    @property
    def x(self) -> int:
        return self.__x

    @x.setter
    def x(self, x: int) -> None:
        raise ValueError('You can\'t change cell coordinate')

    @property
    def y(self) -> int:
        return self.__y

    @y.setter
    def y(self, y: int) -> None:
        raise ValueError('You can\'t change cell coordinate')

    @property
    def color(self) -> str:
        return self.__color

    @color.setter
    def color(self, color: str) -> None:
        raise ValueError('You can\'t change cell color')

    @property
    def target(self) -> int:
        return self.__target

    @target.setter
    def target(self, target: int) -> None:
        raise ValueError('You can\'t change cell target')

    @property
    def neighbors(self) -> list['Cell']:
        return [
            cell for cell in [self.front, self.back, self.left, self.right]
            if cell
        ]

    def generate_mail(self, sprites_mail: pygame.sprite.Group, render_mode: str|None) -> None:
        mail = Mail(random.choice(range(1, 10)), self, render_mode)
        self.mail = mail
        sprites_mail.add(mail)

    def draw(self, surface: pygame.Surface) -> None:

        pygame.draw.rect(
            surface, COLOR2RBG[self.color],
            ((self.x + 5) * CELL_SIZE[0],
             (self.y + 1) * CELL_SIZE[1], CELL_SIZE[0], CELL_SIZE[1]))
        pygame.draw.rect(
            surface, (0, 0, 0),
            ((self.x + 5) * CELL_SIZE[0],
             (self.y + 1) * CELL_SIZE[1], CELL_SIZE[0], CELL_SIZE[1]), 1)
        if self.target:
            target_font = pygame.font.SysFont(None, 64)
            target_image = target_font.render(str(self.target), True,
                                              (0, 0, 0))
            surface.blit(target_image,
                         ((self.x + 5) * CELL_SIZE[0] +
                          (CELL_SIZE[0] - target_image.get_width()) / 2,
                          (self.y + 1) * CELL_SIZE[1] +
                          (CELL_SIZE[1] - target_image.get_height()) / 2))
            
class Board:

    """
    A object representing game board.
    """

    def __init__(self, colors_map: str, targets_map: str) -> None:
        """
        :param colors_map: csv file name for color map. Each element define color of each cell.
        :type colors_map: str
        :param targets_map: csv file name for target map. Each element define target number of each cell. A non-zero numer corresponds to the index of the mail that the location receives.
        :type targets_map: str
        """
        self.__load_from_file(colors_map, targets_map)
        self.size = len(self.cells[0])

        self.yellow_cells = self.__get_cells_by_color('y')
        self.red_cells = self.__get_cells_by_color('r')
        self.green_cells = self.__get_cells_by_color('gr')
        self.blue_cells = self.__get_cells_by_color('b')
        self.white_cells = self.__get_cells_by_color('w')

    # allow us access cell by coordinate
    def __getitem__(self, coordinate: tuple[int, int]) -> Cell:
        return self.cells[coordinate[1]][coordinate[0]]

    def __get_cells_by_color(self, color: str) -> list[Cell]:
        return [
            cell for row_cell in self.cells for cell in row_cell
            if cell.color == color
        ]

    def __load_from_file(self, colors_map: str, targets_map: str) -> None:

        #two dimension list of Cell
        self.cells: list[list[Cell]] = []

        colors_map_file = open(colors_map, mode='r', encoding="utf-8")
        targets_map_file = open(targets_map, mode='r', encoding="utf-8")

        color_matrix = csv.reader(colors_map_file)
        target_matrix = csv.reader(targets_map_file)

        #create cells with given colors and targets in csv files
        for i, (color_row,
                target_row) in enumerate(zip(color_matrix, target_matrix)):
            self.cells.append([])
            for j, (color, target) in enumerate(zip(color_row, target_row)):
                self.cells[-1].append(
                    Cell(i, j, color=color, target=int(target)))

        colors_map_file.close()
        targets_map_file.close()

        #set for each cell its adjacent
        for i, _ in enumerate(self.cells):
            for j, _ in enumerate(self.cells[i]):
                if (i - 1) >= 0:
                    self.cells[i][j].front = self.cells[i - 1][j]
                if (i + 1) < len(self.cells[i]):
                    self.cells[i][j].back = self.cells[i + 1][j]
                if (j + 1) < len(self.cells[i]):
                    self.cells[i][j].right = self.cells[i][j + 1]
                if (j - 1) >= 0:
                    self.cells[i][j].left = self.cells[i][j - 1]

    @property
    def cannot_step(self) -> list[Cell]:
        return [
            cell for cells in self.cells for cell in cells
            if (cell.robot or cell.color == 'r' or cell.color == 'y'
                or cell.color == 'gr')
        ]

    def reset(self) -> None:
        for cells in self.cells:
            for cell in cells:
                cell.robot = None
                cell.mail = None

class Robot(pygame.sprite.Sprite):

    """
    A object representing the robot.
    """

    def __init__(self,
                 pos: Cell,
                 index: int,
                 color: str,
                 sprites_group: pygame.sprite.Group,
                 clock: Clock,
                 mail: Mail | None = None,
                 count_mail: int = 0,
                 battery: int = MAXIMUM_ROBOT_BATTERY,
                 allowed_step_per_turn: int = 1,
                 render_mode: str|None = None) -> None:
        
        r"""
        :param pos: current location of the robot.
        :type pos: Cell
        :param index: the index of the robot. It can't be change.
        :type index: int
        :param color: the color of the robot.
        :type color: str
        :param sprites_group: group of mails. We need to add new mail to this group when robot pick up a mail and leaves green cell.
        :type sprites_group: pygame.sprite.Group
        :param clock: the game clock. For each step of the robot time increases by $\delta t$.
        :type clock: Clock
        :param mail: the mail that robot are carring.
        :type mail: Mail or None
        :param count_mail: number of deliveried mails by robot.
        :type count_mail: int
        :param battery: robot battery.
        :type battery: int
        :param allowed_step_per_turn: variable to control the number of possible steps on each player turn.
        :type allowed_step_per_turn: int
        :param render_mode: the render mode. It can be None or `human`.
        :type render_mode: str or None
        """

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
        assert self.color in COLOR_MAP.keys()
        if self.color == 'b':
            self.image = pygame.image.load('images/blue_robot.png')
        if self.color == 'r':
            self.image = pygame.image.load('images/red_robot.png')
        if self.color == 'y':
            self.image = pygame.image.load('images/yellow_robot.png')
        if self.color == 'gr':
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
    def state(self) -> dict[str, typing.Any]:
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
    def observation(self) -> np.ndarray:
        mail = self.mail.mail_number if self.mail else 0
        return np.hstack([np.eye(9, dtype=np.int8)[self.pos.x], np.eye(9, dtype=np.int8)[self.pos.y], np.eye(10, dtype=np.int8)[mail]])
    
    @property
    def is_charged(self) -> bool:
        return self.pos.color == 'b'

    @property
    def rect(self) -> pygame.Rect:
        rect = self.image.get_rect()
        rect.topleft = ((self.pos.x + 5) * CELL_SIZE[0],
                        (self.pos.y + 1) * CELL_SIZE[1])
        return rect

    def move_up(self) -> tuple[bool, float]:
        reward = DEFAULT_REWARD
        if self.allowed_step_per_turn and self.battery:
            if self.is_legal_moves(Action.GO_AHEAD):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail(self.sprites_group, self.render_mode)
                self.pos = self.pos.front
                self.pos.robot = self
                self.allowed_step_per_turn -= 1
                self.battery -= 1
                log.info(
                    f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go up to position ({self.pos.x},{self.pos.y})'
                )
                if self.mail:
                    self.mail.pos = self.pos
                if self.pick_up(): 
                    reward = REWARD_FOR_PICK_UP_MAIL
                if self.drop_off(): 
                    reward = REWARD_FOR_DROP_OFF_MAIL
                self.clock.up()
                return True, reward
        return False, reward

    def move_down(self) -> tuple[bool, float]:
        reward = DEFAULT_REWARD
        if self.allowed_step_per_turn and self.battery:
            if self.is_legal_moves(Action.GO_BACK):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail(self.sprites_group, self.render_mode)
                self.pos = self.pos.back
                self.pos.robot = self
                self.allowed_step_per_turn -= 1
                self.battery -= 1
                log.info(
                    f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go down to position ({self.pos.x},{self.pos.y})'
                )
                if self.mail:
                    self.mail.pos = self.pos
                if self.pick_up(): 
                    reward = REWARD_FOR_PICK_UP_MAIL
                if self.drop_off(): 
                    reward = REWARD_FOR_DROP_OFF_MAIL
                self.clock.up()
                return True, reward
        return False, reward

    def move_right(self) -> tuple[bool, float]:
        reward = DEFAULT_REWARD
        if self.allowed_step_per_turn and self.battery:
            if self.is_legal_moves(Action.TURN_RIGHT):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail(self.sprites_group, self.render_mode)
                self.pos = self.pos.right
                self.pos.robot = self
                self.allowed_step_per_turn -= 1
                self.battery -= 1
                log.info(
                    f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go left to position ({self.pos.x},{self.pos.y})'
                )
                if self.mail:
                    self.mail.pos = self.pos
                if self.pick_up(): 
                    reward = REWARD_FOR_PICK_UP_MAIL
                if self.drop_off(): 
                    reward = REWARD_FOR_DROP_OFF_MAIL
                self.clock.up()
                return True, reward
        return False, reward

    def move_left(self) -> tuple[bool, float]:
        reward = DEFAULT_REWARD
        if self.allowed_step_per_turn and self.battery:
            if self.is_legal_moves(Action.TURN_LEFT):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail(self.sprites_group, self.render_mode)
                self.pos = self.pos.left
                self.pos.robot = self
                self.allowed_step_per_turn -= 1
                self.battery -= 1
                log.info(
                    f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go right to position ({self.pos.x},{self.pos.y})'
                )
                if self.mail:
                    self.mail.pos = self.pos
                if self.pick_up(): 
                    reward = REWARD_FOR_PICK_UP_MAIL
                if self.drop_off(): 
                    reward = REWARD_FOR_DROP_OFF_MAIL
                self.clock.up()
                return True, reward
        return False, reward

    def pick_up(self) -> bool:
        if not self.mail and self.pos.color == 'gr':
            self.mail = self.pos.mail
            log.info(
                f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} pick up mail {self.mail.mail_number}'
            )
            return True
        return False

    def drop_off(self) -> bool | Mail:
        if self.mail and self.pos.color == 'y':
            deliveried_mail = self.mail
            self.mail.kill()
            self.mail = None
            self.count_mail += 1
            log.info(
                f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} drop off mail {deliveried_mail.mail_number}'
            )
            return deliveried_mail
        return False

    def charge(self) -> None:
        self.battery += BATERRY_UP_PER_STEP
        if self.battery > MAXIMUM_ROBOT_BATTERY:
            self.battery = MAXIMUM_ROBOT_BATTERY
    
    def reset(self, pos: Cell) -> None:
        self.pos = pos
        self.pos.robot = self
        self.mail = None
        self.count_mail = 0
        self.battery = MAXIMUM_ROBOT_BATTERY
        self.allowed_step_per_turn = 1

    def step(self, action: int) -> tuple[bool, float]:
        if action == Action.DO_NOTHING:
            return False, DEFAULT_REWARD
        if action == Action.GO_AHEAD:
            return self.move_up()
        if action == Action.GO_BACK:
            return self.move_down()
        if action == Action.TURN_LEFT:
            return self.move_left()
        if action == Action.TURN_RIGHT:
            return self.move_right()
        return False, DEFAULT_REWARD
    
    def is_legal_moves(self, action: int) -> bool:
        if action == Action.DO_NOTHING:
            return True
        if action == Action.GO_AHEAD:
            if self.pos.front:
                if self.pos.front.color != 'r' and self.pos.front.robot is None and (
                    self.pos.front.color != 'y' or (self.mail and self.pos.front.target == self.mail.mail_number)) and (
                    self.pos.front.color != 'gr' or self.mail is None):
                    return True
            
        if action == Action.GO_BACK:
            if self.pos.back:
                if self.pos.back.color != 'r' and self.pos.back.robot is None and (
                    self.pos.back.color != 'y' or (self.mail and self.pos.back.target == self.mail.mail_number)) and (
                    self.pos.back.color != 'gr' or self.mail is None):
                    return True
                
        if action == Action.TURN_LEFT:
            if self.pos.left:
                if self.pos.left.color != 'r' and self.pos.left.robot is None and (
                    self.pos.left.color != 'y' or (self.mail and self.pos.left.target == self.mail.mail_number)) and (
                    self.pos.left.color != 'gr' or self.mail is None):
                    return True
                
        if action == Action.TURN_RIGHT:
            if self.pos.right:
                if self.pos.right.color != 'r' and self.pos.right.robot is None and (
                    self.pos.right.color != 'y' or (self.mail and self.pos.right.target == self.mail.mail_number)) and (
                    self.pos.right.color != 'gr' or self.mail is None):
                    return True
                
        return False
    
    @property
    def mask(self) -> np.ndarray:
        return np.array([int(self.is_legal_moves(action)) for action in range(5)])
    
class Mail(pygame.sprite.Sprite):
    
    """
    A object representing a mail.
    """

    def __init__(self, mail_number: int, pos: Cell, render_mode=None) -> None:
        """
        :param mail_number: the number of the mail, by which the robot delivers to its destination.
        :type mail_number: int
        :param pos: current location of the mail.
        :type pos: Cell
        :param render_mode: the render mode. It can be None or `human`.
        :type render_mode: str or None
        """
        super().__init__()
        self.mail_number = mail_number
        self.pos = pos
        if render_mode == 'human':
            self.image = pygame.transform.scale(
                pygame.image.load('images/mail.png'), CELL_SIZE)
            mail_number_images = pygame.font.SysFont(None, 16).render(
                str(self.mail_number), True, (255, 0, 0))
            self.image.blit(mail_number_images,
                            (0.5 * CELL_SIZE[0], 0.2 * CELL_SIZE[1]))

    @property
    def rect(self) -> pygame.Rect:
        rect = self.image.get_rect()
        rect.topleft = ((self.pos.x + 5) * CELL_SIZE[0],
                        (self.pos.y + 1) * CELL_SIZE[1])
        return rect
    
class Clock:
    
    r"""
    A object measuring game time. For each step of the robot time increases by $\delta t$.
    """

    def __init__(self) -> None:
        self.now = 0

    def up(self) -> None:
        self.now += DELTA_T

    def reset(self) -> None:
        self.now = 0
