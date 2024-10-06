from __future__ import annotations
import os
import random
import csv
import logging as log
import enum

import numpy as np
import pygame

from src.game.consts import *

class Action(enum.IntEnum):
    '''
    Enum for enumeration of the actions.
    '''
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
        """
        The abscissa on the game board. The coordinate origin is at the top left point, positive direction from left to right.
        """
        return self.__x

    @x.setter
    def x(self, x: int) -> None:
        raise ValueError('You can\'t change cell coordinate')

    @property
    def y(self) -> int:
        """
        The ordinate on the game board. The coordinate origin is at the top left point, positive direction from top to bottom.
        """
        return self.__y

    @y.setter
    def y(self, y: int) -> None:
        raise ValueError('You can\'t change cell coordinate')

    @property
    def color(self) -> str:
        """
        Color of this cell.
        """
        return self.__color

    @color.setter
    def color(self, color: str) -> None:
        raise ValueError('You can\'t change cell color')

    @property
    def target(self) -> int:
        """
        Target of this cell.
        """
        return self.__target

    @target.setter
    def target(self, target: int) -> None:
        raise ValueError('You can\'t change cell target')

    @property
    def neighbors(self) -> list['Cell']:
        """
        Returns neighboring cells of this cell.
        """
        return [
            cell for cell in [self.front, self.back, self.left, self.right]
            if cell
        ]

    def generate_mail(self, sprites_mail: pygame.sprite.Group, render_mode: str|None) -> None:
        """
        Genarate a new mail.
        """
        #create new mail-sprite
        self.mail = Mail(random.choice(range(1, 10)), self, render_mode)
        #add mail to respective ground of sprites
        sprites_mail.add(self.mail)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw this cell in a ```pygame.Surface```.
        """
        #draw rectangle of the cell
        pygame.draw.rect(
            surface, COLOR2RBG[self.color],
            ((self.x + 5) * CELL_SIZE[0],
             (self.y + 1) * CELL_SIZE[1], CELL_SIZE[0], CELL_SIZE[1]))
        #draw border
        pygame.draw.rect(
            surface, (0, 0, 0),
            ((self.x + 5) * CELL_SIZE[0],
             (self.y + 1) * CELL_SIZE[1], CELL_SIZE[0], CELL_SIZE[1]), 1)
        #draw target number if it isn't 0 
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

    def reset(self) -> None:
        '''
        Reset board to empty board.
        '''
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
        :param render_mode: the render mode. It can be None or ```'human'```.
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
        self.render_mode = render_mode
        if self.render_mode == 'human':
            self.__set_image()
            self.__set_number_image()
            self.rect = self.image.get_rect()
            self.rect.topleft = ((self.pos.x + 5) * CELL_SIZE[0],
                                 (self.pos.y + 1) * CELL_SIZE[1])

    def __set_image(self) -> None:
        assert self.color in COLOR_MAP.keys(), "Colors of the robot can only be 'b', 'r', 'y', 'gr', 'o'"
        if self.color == 'b':
            self.image = pygame.image.load(os.path.join(os.getcwd(), 'assets', 'images', 'blue_robot.png'))
        elif self.color == 'r':
            self.image = pygame.image.load(os.path.join(os.getcwd(), 'assets', 'images', 'red_robot.png'))
        elif self.color == 'y':
            self.image = pygame.image.load(os.path.join(os.getcwd(), 'assets', 'images', 'yellow_robot.png'))
        elif self.color == 'gr':
            self.image = pygame.image.load(os.path.join(os.getcwd(), 'assets', 'images', 'green_robot.png'))
        elif self.color == 'o':
            self.image = pygame.image.load(os.path.join(os.getcwd(), 'assets', 'images', 'orange_robot.png'))
        self.image = pygame.transform.scale(self.image, CELL_SIZE)

    def __set_number_image(self) -> None:
        robot_number_font = pygame.font.SysFont(None, 16)
        number_img = robot_number_font.render(str(self.index), True, (0, 0, 0))
        self.image.blit(number_img,
                        (0.5 * CELL_SIZE[0] - number_img.get_width() / 2,
                         0.7 * CELL_SIZE[1] - number_img.get_height() / 2))

    @property
    def battery(self) -> int:
        """
        Battery of the robot. It must be positive and less than ```MAXIMUM_ROBOT_BATTERY```.
        """
        return self.__battery
    
    @battery.setter
    def battery(self, battery: int) -> None:
        if battery < 0:
            self.__battery = 0
        elif battery > MAXIMUM_ROBOT_BATTERY:
            self.__battery = MAXIMUM_ROBOT_BATTERY
        else:
            self.__battery = battery

    @property
    def observation(self) -> np.ndarray:
        """
        Observation of the single robot. Each of attributes x, y, mail, battery is normalized and all this concatenated.
        """
        mail = self.mail.mail_number if self.mail else 0
        return np.array([self.pos.x/8, self.pos.y/8, mail/9, self.battery/50], dtype=np.float32)
    
    @property
    def is_charged(self) -> bool:
        """
        Robot is charging or not.
        """
        return self.pos.color == 'b'

    @property
    def next_rect(self) -> pygame.Rect:
        """
        Rectangle to define where to draw robot.
        """
        rect = self.image.get_rect()
        rect.topleft = ((self.pos.x + 5) * CELL_SIZE[0],
                        (self.pos.y + 1) * CELL_SIZE[1])
        return rect
    
    def stand(self) -> tuple[bool, float]:
        """
        Don't move.
        """
        #we assume this action is legal.
        reward = DEFAULT_REWARD
        if self.pos.color == 'b':
            self.charge()
            reward = 0
        return False, reward

    def move_up(self) -> tuple[bool, float]:
        """
        Move forward. Return reward for this move. 
        """
        #we assume this action is legal.
        reward = DEFAULT_REWARD
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.front
        self.pos.robot = self
        self.battery -= 1
        log.info(
            f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go up to position ({self.pos.x},{self.pos.y})'
        )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_MOVING_TO_BLUE
        self.clock.up()
        return True, reward

    def move_down(self) -> tuple[bool, float]:
        """
        Move back. Return reward for this move.
        """
        #we assume this action is legal.
        reward = DEFAULT_REWARD
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.back
        self.pos.robot = self
        self.battery -= 1
        log.info(
            f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go down to position ({self.pos.x},{self.pos.y})'
        )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_MOVING_TO_BLUE
        self.clock.up()
        return True, reward

    def move_right(self) -> tuple[bool, float]:
        """
        Move right. Return reward for this move.
        """
        #we assume this action is legal.
        reward = DEFAULT_REWARD
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.right
        self.pos.robot = self
        self.battery -= 1
        log.info(
            f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go left to position ({self.pos.x},{self.pos.y})'
        )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_MOVING_TO_BLUE
        self.clock.up()
        return True, reward

    def move_left(self) -> tuple[bool, float]:
        """
        Move left. Return reward for this move. 
        """
        #we assume this action is legal.
        reward = DEFAULT_REWARD
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.left
        self.pos.robot = self
        self.battery -= 1
        log.info(
            f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} go right to position ({self.pos.x},{self.pos.y})'
        )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_MOVING_TO_BLUE
        self.clock.up()
        return True, reward

    def pick_up(self) -> None:
        """
        Pick up a mail.
        """
        #we assume this action is legal.
        self.mail = self.pos.mail
        log.info(
            f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} pick up mail {self.mail.mail_number}'
        )

    def drop_off(self) -> None:
        """
        Drop off a mail.
        """
        #we assume this action is legal.
        deliveried_mail = self.mail
        self.mail.kill()
        self.mail = None
        self.count_mail += 1
        log.info(
            f'At t={self.clock.now:04} {COLOR_MAP[self.color]:>5} robot {self.index} drop off mail {deliveried_mail.mail_number}'
        )

    def charge(self) -> None:
        """
        Charge.
        """
        #we assume this action is legal.
        self.battery += BATERRY_UP_PER_STEP
    
    def reset(self, pos: Cell) -> None:
        """
        Reset robot to initial state in ```pos```.
        """
        self.pos = pos
        self.pos.robot = self
        self.mail = None
        self.count_mail = 0
        self.battery = MAXIMUM_ROBOT_BATTERY
        self.rect = self.next_rect

    def step(self, action: int) -> tuple[bool, float]:
        """
        Do robot move base on  ```action```.
        """
        #check if action is legal
        #truly, action from agent always is legal because of action mask
        #we check for case that all actions are illegal
        is_legal_action = self.is_legal_move(action) 
        if not is_legal_action:
            #if all actions are not legal, skip robot's turn
            return False, DEFAULT_REWARD
        if action == Action.GO_AHEAD:
            return self.move_up()
        if action == Action.GO_BACK:
            return self.move_down()
        if action == Action.TURN_LEFT:
            return self.move_left()
        if action == Action.TURN_RIGHT:
            return self.move_right()
        if action == Action.DO_NOTHING:
            return self.stand()
    
    def is_legal_move(self, action: int) -> bool:
        """
        Check if action is legal.
        """

        if action == Action.DO_NOTHING:
            #robot with high battery can't stand in the blue cell
            if self.pos.color == 'b' and self.battery >= MAXIMUM_ROBOT_BATTERY - BATERRY_UP_PER_STEP:
                return False
            #robot without mail can't stand in the yellow cell
            if self.pos.color == 'y' and not self.mail:
                return False
            #robot with mail can't stand in the green cell
            if self.pos.color == 'gr' and self.mail:
                return False
        
        if action == Action.GO_AHEAD:
            #robot can't move if battery is exhausted
            if not self.battery:
                return False
            #if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < 0.8*MAXIMUM_ROBOT_BATTERY:
                return False
            #robot can't move if next cell is none
            if not self.pos.front:
                return False
            #robot can't move if next cell is red
            if self.pos.front.color == 'r':
                return False
            #robot can't move if next cell is not empty
            if self.pos.front.robot:
                return False
            #robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.front.color == 'y':
                if not self.mail:
                    return False
                if self.pos.front.target != self.mail.mail_number:
                    return False
            #robot can't move to green cell if it already has carried a mail
            if self.pos.front.color == 'gr' and self.mail:
                return False
            #robot with high battery can't move to blue cell
            if self.pos.front.color == 'b' and self.battery > BATTERY_TO_CHARGE:
                return False

        if action == Action.GO_BACK:
            #robot can't move if battery is exhausted
            if not self.battery:
                return False
            #if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < 0.8*MAXIMUM_ROBOT_BATTERY:
                return False
            #robot can't move if next cell is none
            if not self.pos.back:
                return False
            #robot can't move if next cell is red
            if self.pos.back.color == 'r':
                return False
            #robot can't move if next cell is not empty
            if self.pos.back.robot:
                return False
            #robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.back.color == 'y':
                if not self.mail:
                    return False
                if self.pos.back.target != self.mail.mail_number:
                    return False
            #robot can't move to green cell if it already has carried a mail
            if self.pos.back.color == 'gr' and self.mail:
                return False
            #robot with high battery can't move to blue cell
            if self.pos.back.color == 'b' and self.battery > BATTERY_TO_CHARGE:
                return False

        if action == Action.TURN_LEFT:
            #robot can't move if battery is exhausted
            if not self.battery:
                return False
            #if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < 0.8*MAXIMUM_ROBOT_BATTERY:
                return False
            #robot can't move if next cell is none
            if not self.pos.left:
                return False
            #robot can't move if next cell is red
            if self.pos.left.color == 'r':
                return False
            #robot can't move if next cell is not empty
            if self.pos.left.robot:
                return False
            #robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.left.color == 'y':
                if not self.mail:
                    return False
                if self.pos.left.target != self.mail.mail_number:
                    return False
            #robot can't move to green cell if it already has carried a mail
            if self.pos.left.color == 'gr' and self.mail:
                return False
            #robot with high battery can't move to blue cell
            if self.pos.left.color == 'b' and self.battery > BATTERY_TO_CHARGE:
                return False
                
        if action == Action.TURN_RIGHT:
            #robot can't move if battery is exhausted
            if not self.battery:
                return False
            #if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < 0.8*MAXIMUM_ROBOT_BATTERY:
                return False
            #robot can't move if next cell is none
            if not self.pos.right:
                return False
            #robot can't move if next cell is red
            if self.pos.right.color == 'r':
                return False
            #robot can't move if next cell is not empty
            if self.pos.right.robot:
                return False
            #robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.right.color == 'y':
                if not self.mail:
                    return False
                if self.pos.right.target != self.mail.mail_number:
                    return False
            #robot can't move to green cell if it already has carried a mail
            if self.pos.right.color == 'gr' and self.mail:
                return False
            #robot with high battery can't move to blue cell
            if self.pos.right.color == 'b' and self.battery > BATTERY_TO_CHARGE:
                return False
                
        return True
    
    @property
    def mask(self) -> np.ndarray:
        """
        Action mask for legal actions.
        """
        return np.array([int(self.is_legal_move(action)) for action in Action], dtype=np.uint8)
    
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
        if render_mode == 'human':
            self.image = pygame.transform.scale(
                pygame.image.load(os.path.join(os.getcwd(), 'assets', 'images','mail.png')), CELL_SIZE)
            mail_number_images = pygame.font.SysFont(None, 16).render(
                str(self.mail_number), True, (255, 0, 0))
            self.image.blit(mail_number_images,
                            (0.5 * CELL_SIZE[0], 0.2 * CELL_SIZE[1]))
            self.rect = self.image.get_rect()
            self.rect.topleft = ((pos.x + 5) * CELL_SIZE[0],
                                 (pos.y + 1) * CELL_SIZE[1])
    
class Clock:
    
    r"""
    A object measuring game time. For each step of the robot time increases by $\delta t$.
    """

    def __init__(self, delta_t: float=1) -> None:
        r"""
        :param delta_t: $\delta t$ - time span that we assume for one move.
        :type delta_t: float
        """
        self.now = 0
        self.delta_t = delta_t

    def up(self) -> None:
        r"""
        Increases time by $\delta t$.
        """
        self.now += self.delta_t

    def reset(self) -> None:
        """
        Reset to zero time.
        """
        self.now = 0