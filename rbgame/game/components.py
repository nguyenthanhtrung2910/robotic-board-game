from __future__ import annotations
import os
import random
import csv
import math
import logging as log
import enum

import numpy as np
import pygame

from rbgame.game.consts import *

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
    A cell in the board.

    .. note::

        All attributes except :py:attr:`mail` after initialization shouldn't be changed.

    :param x: The abscissa on the game board. The coordinate origin is at the top left point, positive direction from left to right.
    :param y: The ordinate on the game board. The coordinate origin is at the top left point, positive direction from top to bottom.
    :param color: The color of the cell. Possible colors are ``'w'`` - white, ``'b'`` - blue,  ``'r'`` - red, ``'y'`` - yellow, ``'gr'`` - green, ``'g'`` - gray.
    :param target: Number of the mail that robot have to delivery to this cell. 0 if cell isn't receiving station.  
    :param robot: The located in this cell robot.
    :param mail: Generated mail in this cell.
    :param front: The front cell of this cell.
    :param back: The back cell of this cell.
    :param left: The left cell of this cell.
    :param right: The right cell of this cell.
    """

    def __init__(
        self,
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
        right: 'Cell | None' = None
    ) -> None:
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

    # equal and hash dunder method for using a Cell as dictionary's key
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
        """
        Returns neighboring cells of this cell.
        """
        return [
            cell for cell in [self.front, self.back, self.left, self.right]
            if cell
        ]

    def generate_mail(self, sprites_mail: pygame.sprite.Group, render_mode: str|None) -> None:
        """
        Generate a new mail and add it to :code:`sprites_mail`.

        :param sprites_mail: Group of sprites to add new mail.
        :param render_mode: Render mode of new generated mail.
        """
        # create new mail-sprite
        self.mail = Mail(random.choice(range(1, 10)), self, render_mode)
        # add mail to respective ground of sprites
        sprites_mail.add(self.mail)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw this cell in a surface.

        :param surface: Surface to draw this cell in.
        """
        # draw rectangle of the cell
        pygame.draw.rect(
            surface, MAP_COLORS[self.color],
            ((self.x + 1) * CELL_SIZE[0],
             (self.y + 1) * CELL_SIZE[1], CELL_SIZE[0], CELL_SIZE[1]))
        # draw border
        pygame.draw.rect(
            surface, (0, 0, 0),
            ((self.x + 1) * CELL_SIZE[0],
             (self.y + 1) * CELL_SIZE[1], CELL_SIZE[0], CELL_SIZE[1]), 1)
        # draw target number if it isn't 0 
        if self.target:
            target_font = pygame.font.SysFont(None, 64)
            target_image = target_font.render(str(self.target), True,
                                              (0, 0, 0))
            surface.blit(target_image,
                         ((self.x + 1) * CELL_SIZE[0] +
                          (CELL_SIZE[0] - target_image.get_width()) / 2,
                          (self.y + 1) * CELL_SIZE[1] +
                          (CELL_SIZE[1] - target_image.get_height()) / 2))
            
class Board:

    """
    A object representing game board. It is set of :py:class:`Cell`.

    :param colors_map: csv file name for color map. 
                       Each element define :py:attr:`color` of each :py:class:`Cell`.
    :param targets_map: csv file name for target map. 
                        Each element define :py:attr:`target` of each :py:class:`Cell`. 
    """

    def __init__(self, colors_map: str, targets_map: str) -> None:

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

        # two dimension list of Cell
        self.cells: list[list[Cell]] = []

        colors_map_file = open(colors_map, mode='r', encoding="utf-8")
        targets_map_file = open(targets_map, mode='r', encoding="utf-8")

        color_matrix = csv.reader(colors_map_file)
        target_matrix = csv.reader(targets_map_file)

        # create cells with given colors and targets in csv files
        for i, (color_row,
                target_row) in enumerate(zip(color_matrix, target_matrix)):
            self.cells.append([])
            for j, (color, target) in enumerate(zip(color_row, target_row)):
                self.cells[-1].append(
                    Cell(i, j, color=color, target=int(target)))

        colors_map_file.close()
        targets_map_file.close()

        # set for each cell its adjacent
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
    Robot in the board.

    .. note::

        Attributes :py:attr:`index` and :py:attr:`color` after initialization shouldn't be changed.

    :param pos: Current position of the robot.
    :param index: The index of the robot.
    :param color: The color of the robot.
    :param sprites_group: Group of mails. We need to add new mail to this group when robot pick up a mail and leaves green cell.
    :param clock: The game clock. For each step of the robot, time increases by :math:`\\Delta t`.
    :param mail: The mail that robot are carring.
    :param count_mail: Number of deliveried mails by robot.
    :param battery: The battery.
    :param with_battery: Battery is considered or not.
    :param render_mode: The render mode. It can be :py:data:`None` or :code:`'human'`.
    :param log _to_file: Log game process to file or not.
    """


    def __init__(
        self,
        pos: Cell,
        index: int,
        color: str,
        sprites_group: pygame.sprite.Group,
        clock: Clock,
        mail: Mail | None = None,
        count_mail: int = 0,
        battery: int = MAXIMUM_ROBOT_BATTERY,
        with_battery: bool = True,
        render_mode: str|None = None,
        log_to_file: bool = False,
    ) -> None:
        super().__init__()
        self.pos = pos
        self.pos.robot = self
        self.index = index
        self.color = color
        self.sprites_group = sprites_group
        self.clock = clock
        self.mail = mail
        self.count_mail = count_mail
        self.__battery = battery
        self.with_battery = with_battery
        self.render_mode = render_mode
        self.log = log_to_file 

        # an variable to count how many times robot stands still
        self.stand_times = 0

        if self.render_mode == 'human':
            self.__set_image()
            self.__set_number_image()
            self.rect = self.image.get_rect()
            self.rect.topleft = ((self.pos.x + 1) * CELL_SIZE[0],
                                 (self.pos.y + 1) * CELL_SIZE[1])

    def __set_image(self) -> None:
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        if self.color == 'b':
            self.image = pygame.image.load(os.path.join(parent_dir, 'assets', 'images', 'blue_robot.png'))
        elif self.color == 'r':
            self.image = pygame.image.load(os.path.join(parent_dir, 'assets', 'images', 'red_robot.png'))
        elif self.color == 'p':
            self.image = pygame.image.load(os.path.join(parent_dir, 'assets', 'images', 'purple_robot.png'))
        elif self.color == 'gr':
            self.image = pygame.image.load(os.path.join(parent_dir, 'assets', 'images', 'green_robot.png'))
        elif self.color == 'o':
            self.image = pygame.image.load(os.path.join(parent_dir, 'assets', 'images', 'orange_robot.png'))
        elif self.color == 'pi':
            self.image = pygame.image.load(os.path.join(parent_dir, 'assets', 'images', 'pink_robot.png'))
        else:
            raise ValueError("Colors of the robot can only be 'b', 'r', 'p', 'gr', 'o', 'pi'")
        self.image = pygame.transform.scale(self.image, CELL_SIZE)

    def __set_number_image(self) -> None:
        robot_number_font = pygame.font.SysFont(None, 16)
        number_img = robot_number_font.render(str(self.index), True, (0, 0, 0))
        self.image.blit(number_img,
                        (0.5 * CELL_SIZE[0] - number_img.get_width() / 2,
                         0.7 * CELL_SIZE[1] - number_img.get_height() / 2))

    @property
    def battery(self) -> int:
        return math.ceil(self.__battery)
    
    @property
    def inner_battery(self) -> int:
        return self.__battery
    
    @inner_battery.setter
    def inner_battery(self, battery: int) -> None:
        if not self.with_battery:
            return
        if battery < 0:
            self.__battery = 0
        elif battery > MAXIMUM_ROBOT_BATTERY:
            self.__battery = MAXIMUM_ROBOT_BATTERY
        else:
            self.__battery = battery

    @property
    def observation(self) -> np.ndarray:
        """
        Observation of the single robot. Each of attributes x, y, mail, battery is normalized to forward in neural network.
        """
        mail = self.mail.mail_number if self.mail else 0
        return np.array([self.pos.x/8, self.pos.y/8, mail/9, self.battery/10], dtype=np.float32) if self.with_battery \
            else np.array([self.pos.x/8, self.pos.y/8, mail/9], dtype=np.float32)
    
    @property
    def is_charged(self) -> bool:
        """
        Robot is charging or not.
        """
        return self.pos.color == 'b'

    @property
    def next_rect(self) -> pygame.Rect:
        """
        Next rectangle, where we should draw it after its movement.
        """
        rect = self.image.get_rect()
        rect.topleft = ((self.pos.x + 1) * CELL_SIZE[0],
                        (self.pos.y + 1) * CELL_SIZE[1])
        return rect
    
    def stand(self) -> tuple[bool, float]:
        """
        Don't move. Charge if possible.

        :return: Two value. First, have some movements or not. Second, the reward.
        """
        # we assume this action is legal.
        reward = DEFAULT_REWARD
        self.stand_times += 1
        if self.pos.color == 'b':
            self.charge()
            reward = 0
        return False, reward

    def move_up(self) -> tuple[bool, float]:
        """
        Move forward. Pick up or drop off mail if possible.

        :return: Two value. First, have some movements or not. Second, the reward.
        """
        # we assume this action is legal.
        reward = DEFAULT_REWARD
        self.stand_times = 0
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.front
        self.pos.robot = self
        self.inner_battery -= BATTERY_PER_STEP if self.inner_battery > 2 else BATTERY_PER_STEP/2
        if self.log:
            log.info(
                f'At t={self.clock.now:04} {COLOR2STR[self.color]:>5} robot {self.index} go up to position ({self.pos.x},{self.pos.y})'
            )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_REACHING_BLUE
        self.clock.up()
        return True, reward

    def move_down(self) -> tuple[bool, float]:
        """
        Move back. Pick up or drop off mail if possible.
        
        :return: Two value. First, have some movements or not. Second, the reward.
        """
        # we assume this action is legal.
        reward = DEFAULT_REWARD
        self.stand_times = 0
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.back
        self.pos.robot = self
        self.inner_battery -= BATTERY_PER_STEP if self.inner_battery > 2 else BATTERY_PER_STEP/2
        if self.log:
            log.info(
                f'At t={self.clock.now:04} {COLOR2STR[self.color]:>5} robot {self.index} go down to position ({self.pos.x},{self.pos.y})'
            )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_REACHING_BLUE
        self.clock.up()
        return True, reward

    def move_right(self) -> tuple[bool, float]:
        """
        Move right. Pick up or drop off mail if possible.

        :return: Two value. First, have some movements or not. Second, the reward.
        """
        # we assume this action is legal.
        reward = DEFAULT_REWARD
        self.stand_times = 0
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.right
        self.pos.robot = self
        self.inner_battery -= BATTERY_PER_STEP if self.inner_battery > 2 else BATTERY_PER_STEP/2
        if self.log:
            log.info(
                f'At t={self.clock.now:04} {COLOR2STR[self.color]:>5} robot {self.index} go left to position ({self.pos.x},{self.pos.y})'
            )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_REACHING_BLUE
        self.clock.up()
        return True, reward

    def move_left(self) -> tuple[bool, float]:
        """
        Move left. Pick up or drop off mail if possible.

        :return: Two value. First, have some movements or not. Second, the reward.
        """
        # we assume this action is legal.
        reward = DEFAULT_REWARD
        self.stand_times = 0
        self.pos.robot = None
        if self.pos.color == 'gr':
            self.pos.generate_mail(self.sprites_group, self.render_mode)
        self.pos = self.pos.left
        self.pos.robot = self
        self.inner_battery -= BATTERY_PER_STEP if self.inner_battery > 2 else BATTERY_PER_STEP/2
        if self.log:
            log.info(
                f'At t={self.clock.now:04} {COLOR2STR[self.color]:>5} robot {self.index} go right to position ({self.pos.x},{self.pos.y})'
            )
        if self.pos.color == 'gr':
            self.pick_up()
            reward = REWARD_FOR_PICK_UP_MAIL
        elif self.pos.color == 'y':
            self.drop_off()
            reward = REWARD_FOR_DROP_OFF_MAIL
        elif self.pos.color == 'b':
            reward = REWARD_FOR_REACHING_BLUE
        self.clock.up()
        return True, reward

    def pick_up(self) -> None:
        """
        Pick up a mail.
        """
        # we assume this action is legal.
        self.mail = self.pos.mail
        if self.log:
            log.info(
                f'At t={self.clock.now:04} {COLOR2STR[self.color]:>5} robot {self.index} pick up mail {self.mail.mail_number}'
            )

    def drop_off(self) -> None:
        """
        Drop off a mail.
        """
        # we assume this action is legal.
        deliveried_mail = self.mail
        self.mail.kill()
        self.mail = None
        self.count_mail += 1
        if self.log:
            log.info(
                f'At t={self.clock.now:04} {COLOR2STR[self.color]:>5} robot {self.index} drop off mail {deliveried_mail.mail_number}'
            )

    def charge(self) -> None:
        """
        Charge.
        """
        # we assume this action is legal.
        self.inner_battery += BATTERY_UP_PER_CHARGE
    
    def reset(self, pos: Cell) -> None:
        """
        Reset robot to initial state in :code:`pos`.

        :param pos: Position to place robot.
        """
        self.pos = pos
        self.pos.robot = self
        self.mail = None
        self.count_mail = 0
        self.inner_battery = MAXIMUM_ROBOT_BATTERY
        if self.render_mode == 'human':
            self.rect = self.next_rect

    def step(self, action: int) -> tuple[bool, float]:
        """
        Do robot move base on  :code:`action`.

        :param action: Action to execute.
        :return: Two value. First, have some movements or not. Second, the reward.
        """
        # check if action is legal
        # truly, action from agent always is legal because of action mask
        # we check for case that all actions are illegal
        is_legal_action = self.is_legal_move(action) 
        if not is_legal_action:
            # if all actions are not legal, skip robot's turn
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

        :param action: Action to check.
        :return: Possibility of :code:`action`  
        """

        if action == Action.DO_NOTHING:
            # robot with high battery can't stand in the blue cell
            if self.pos.color == 'b' and self.battery >= MAXIMUM_ROBOT_BATTERY - 1:
                return False
            # robot without mail can't stand in the yellow cell
            if self.pos.color == 'y' and not self.mail:
                return False
            # robot with mail can't stand in the green cell
            if self.pos.color == 'gr' and self.mail:
                return False
            # robot with high battery can't stand waiting for charging
            if any([cell.color == 'b' for cell in self.pos.neighbors]) and self.battery > PERCENT_BATTERY_TO_CHARGE*MAXIMUM_ROBOT_BATTERY:
                return False
            # robot, stucked between two yellow cells in the edge of the board, can't stand
            if sum([int(cell.color == 'y' or cell.color == 'r') for cell in self.pos.neighbors]) == 2:
                return False
            # robot can't stand constantly
            if self.pos.color != 'b' and self.stand_times >= 5:
                return False
        
        if action == Action.GO_AHEAD:
            # robot can't move if battery is exhausted
            if not self.battery:
                return False
            # if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < PERCENT_BATTERY_TO_LEAVE*MAXIMUM_ROBOT_BATTERY:
                return False
            # robot can't move if next cell is none
            if not self.pos.front:
                return False
            # robot can't move if next cell is red
            if self.pos.front.color == 'r':
                return False
            # robot can't move if next cell is not empty
            if self.pos.front.robot:
                return False
            # robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.front.color == 'y':
                if not self.mail:
                    return False
                if self.pos.front.target != self.mail.mail_number:
                    return False
            # robot can't move to green cell if it already has carried a mail
            if self.pos.front.color == 'gr' and self.mail:
                return False
            # robot with high battery can't move to blue cell
            if self.pos.front.color == 'b' and self.battery > PERCENT_BATTERY_TO_CHARGE*MAXIMUM_ROBOT_BATTERY:
                return False
            if self.pos.color != 'y' and sum([int(cell.color == 'y' or cell.color == 'r') for cell in self.pos.front.neighbors]) == 2:
                if not self.mail:
                    return False
                if self.mail.mail_number not in [cell.target for cell in self.pos.front.neighbors]:
                    return False


        if action == Action.GO_BACK:
            # robot can't move if battery is exhausted
            if not self.battery:
                return False
            # if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < PERCENT_BATTERY_TO_LEAVE*MAXIMUM_ROBOT_BATTERY:
                return False
            # robot can't move if next cell is none
            if not self.pos.back:
                return False
            # robot can't move if next cell is red
            if self.pos.back.color == 'r':
                return False
            # robot can't move if next cell is not empty
            if self.pos.back.robot:
                return False
            # robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.back.color == 'y':
                if not self.mail:
                    return False
                if self.pos.back.target != self.mail.mail_number:
                    return False
            # robot can't move to green cell if it already has carried a mail
            if self.pos.back.color == 'gr' and self.mail:
                return False
            # robot with high battery can't move to blue cell
            if self.pos.back.color == 'b' and self.battery > PERCENT_BATTERY_TO_CHARGE*MAXIMUM_ROBOT_BATTERY:
                return False
            # robot avoid go to corner if don't need drop off mail
            if self.pos.color != 'y' and sum([int(cell.color == 'y' or cell.color == 'r') for cell in self.pos.back.neighbors]) == 2:
                if not self.mail:
                    return False
                if self.mail.mail_number not in [cell.target for cell in self.pos.back.neighbors]:
                    return False

        if action == Action.TURN_LEFT:
            # robot can't move if battery is exhausted
            if not self.battery:
                return False
            # if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < PERCENT_BATTERY_TO_LEAVE*MAXIMUM_ROBOT_BATTERY:
                return False
            # robot can't move if next cell is none
            if not self.pos.left:
                return False
            # robot can't move if next cell is red
            if self.pos.left.color == 'r':
                return False
            # robot can't move if next cell is not empty
            if self.pos.left.robot:
                return False
            # robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.left.color == 'y':
                if not self.mail:
                    return False
                if self.pos.left.target != self.mail.mail_number:
                    return False
            # robot can't move to green cell if it already has carried a mail
            if self.pos.left.color == 'gr' and self.mail:
                return False
            # robot with high battery can't move to blue cell
            if self.pos.left.color == 'b' and self.battery > PERCENT_BATTERY_TO_CHARGE*MAXIMUM_ROBOT_BATTERY:
                return False
            if self.pos.color != 'y' and sum([int(cell.color == 'y' or cell.color == 'r') for cell in self.pos.left.neighbors]) == 2:
                if not self.mail:
                    return False
                if self.mail.mail_number not in [cell.target for cell in self.pos.left.neighbors]:
                    return False
                               
        if action == Action.TURN_RIGHT:
            # robot can't move if battery is exhausted
            if not self.battery:
                return False
            # if robot is charging, it can't move until battery is nearly full
            if self.pos.color == 'b' and self.battery < PERCENT_BATTERY_TO_LEAVE*MAXIMUM_ROBOT_BATTERY:
                return False
            # robot can't move if next cell is none
            if not self.pos.right:
                return False
            # robot can't move if next cell is red
            if self.pos.right.color == 'r':
                return False
            # robot can't move if next cell is not empty
            if self.pos.right.robot:
                return False
            # robot can't move to yellow cell if it don't carry a mail or carried mail not match with cell target
            if self.pos.right.color == 'y':
                if not self.mail:
                    return False
                if self.pos.right.target != self.mail.mail_number:
                    return False
            # robot can't move to green cell if it already has carried a mail
            if self.pos.right.color == 'gr' and self.mail:
                return False
            # robot with high battery can't move to blue cell
            if self.pos.right.color == 'b' and self.battery > PERCENT_BATTERY_TO_CHARGE*MAXIMUM_ROBOT_BATTERY:
                return False
            if self.pos.color != 'y' and sum([int(cell.color == 'y' or cell.color == 'r') for cell in self.pos.right.neighbors]) == 2:
                if not self.mail:
                    return False
                if self.mail.mail_number not in [cell.target for cell in self.pos.right.neighbors]:
                    return False 
        return True
    
    @property
    def mask(self) -> np.ndarray:
        """
        Action mask for legal actions.
        """
        return np.array([self.is_legal_move(action) for action in Action], dtype=np.uint8)
    
class Mail(pygame.sprite.Sprite):
    """
    A object representing a mail.

    :param mail_number: The number of the mail.
    :param pos: Current location of the mail.
    :param render_mode: The render mode. It can be None or :code:`'human'`.
    """

    def __init__(self, mail_number: int, pos: Cell, render_mode=None) -> None:
        super().__init__()
        self.mail_number = mail_number
        if render_mode == 'human':
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            self.image = pygame.transform.scale(
                pygame.image.load(os.path.join(parent_dir, 'assets', 'images','mail.png')), CELL_SIZE)
            mail_number_images = pygame.font.SysFont(None, 16).render(
                str(self.mail_number), True, (255, 0, 0))
            self.image.blit(mail_number_images,
                            (0.5 * CELL_SIZE[0], 0.2 * CELL_SIZE[1]))
            self.rect = self.image.get_rect()
            self.rect.topleft = ((pos.x + 1) * CELL_SIZE[0],
                                 (pos.y + 1) * CELL_SIZE[1])
    
class Clock:
    """
    A object measuring game time. For each step of the robot time increases by :math:`\\Delta t`.

    :param delta_t: :math:`\\Delta t` - time span that we assume for one move.
    """
    def __init__(self, delta_t: float=1) -> None:
        self.now = 0
        self.delta_t = delta_t

    def up(self) -> None:
        """
        Increases time by :math:`\\Delta t`.
        """
        self.now += self.delta_t

    def reset(self) -> None:
        """
        Reset to zero time.
        """
        self.now = 0
