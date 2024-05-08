from __future__ import annotations

from Agents import VirtualCell
from Agents import VirtualBoard
from Game.consts import *


class VirtualRobot:

    def __init__(self,
                 pos: VirtualCell.VirtualCell,
                 index: int,
                 color: str,
                 mail: int = 0,
                 count_mail: int = 0,
                 battery: int = MAXIMUM_ROBOT_BATTERY):
        self.pos = pos
        self.pos.robot = self
        self.index = index
        self.color = color
        self.mail = mail
        self.count_mail = count_mail
        self.battery = battery

    @property
    def is_charged(self) -> bool:
        return self.pos.color == 'b'

    def move_up(self) -> bool:
        if self.battery:
            if self.pos.front:
                if self.pos.front.color != 'r' and not self.pos.front.robot and (
                        self.pos.front.color != 'y' or
                    (self.mail and self.pos.front.target == self.mail)) and (
                        self.pos.front.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail()
                    self.pos = self.pos.front
                    self.pos.robot = self
                    self.battery -= 1
                    self.pick_up()
                    self.drop_off()
                    return True
        return False

    def move_down(self) -> bool:
        if self.battery:
            if self.pos.back:
                if self.pos.back.color != 'r' and not self.pos.back.robot and (
                        self.pos.back.color != 'y' or
                    (self.mail and self.pos.back.target == self.mail)) and (
                        self.pos.back.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail()
                    self.pos = self.pos.back
                    self.pos.robot = self
                    self.battery -= 1
                    self.pick_up()
                    self.drop_off()
                    return True
        return False

    def move_right(self) -> bool:
        if self.battery:
            if self.pos.right:
                if self.pos.right.color != 'r' and not self.pos.right.robot and (
                        self.pos.right.color != 'y' or
                    (self.mail and self.pos.right.target == self.mail)) and (
                        self.pos.right.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail()
                    self.pos = self.pos.right
                    self.pos.robot = self
                    self.battery -= 1
                    self.pick_up()
                    self.drop_off()
                    return True
        return False

    def move_left(self) -> bool:
        if self.battery:
            if self.pos.left:
                if self.pos.left.color != 'r' and not self.pos.left.robot and (
                        self.pos.left.color != 'y' or
                    (self.mail and self.pos.left.target == self.mail)) and (
                        self.pos.left.color != 'gr' or self.mail is None):
                    self.pos.robot = None
                    if self.pos.color == 'gr':
                        self.pos.generate_mail()
                    self.pos = self.pos.left
                    self.pos.robot = self
                    self.battery -= 1
                    self.pick_up()
                    self.drop_off()
                    return True
        return False

    def pick_up(self) -> bool:
        if not self.mail and self.pos.color == 'gr':
            self.mail = self.pos.mail
            return True
        return False

    def drop_off(self) -> bool | int:
        if self.mail and self.pos.color == 'y':
            deliveried_mail = self.mail
            self.mail = 0
            self.count_mail += 1
            return deliveried_mail
        return False

    def charge(self) -> None:
        self.battery += BATERRY_UP_PER_STEP
        if self.battery > MAXIMUM_ROBOT_BATTERY:
            self.battery = MAXIMUM_ROBOT_BATTERY
    
    def reset(self, pos: VirtualCell.VirtualCell) -> None:
        self.pos = pos
        self.pos.robot = self
        self.mail = 0
        self.count_mail = 0
        self.battery = MAXIMUM_ROBOT_BATTERY

    def get_destination(
        self,
        board: VirtualBoard.VirtualBoard,
        blocked: list[VirtualCell.VirtualCell] = []
    ) -> VirtualCell.VirtualCell:
        if self.battery <= 30:
            return min(
                [cell for cell in board.blue_cells if cell not in blocked],
                key=lambda blue_cell: VirtualBoard.VirtualBoard.heuristic(
                    self.pos, blue_cell))
        else:
            if self.mail:
                for yellow_cell in board.yellow_cells:
                    if yellow_cell.target == self.mail:
                        return yellow_cell
            else:
                return min([
                    cell for cell in board.green_cells if cell not in blocked
                ],
                           key=lambda green_cell: VirtualBoard.VirtualBoard.
                           heuristic(self.pos, green_cell))
        return self.pos
