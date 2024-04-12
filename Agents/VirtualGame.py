from typing import Any
from Agents import VirtualBoard
from Agents import VirtualRobot
from Game.consts import *


class VirtualGame:

    def __init__(self, board: VirtualBoard.VirtualBoard, required_mail: int,
                 state: dict[str, list[dict[str, Any]] | list[int]]) -> None:

        self.board = board
        self.required_mail = required_mail
        self.robots: dict[str, list[VirtualRobot.VirtualRobot]] = {}
        for robot_state in state['robots_state']:
            self.robots[robot_state['color']] = []
        for robot_state in state['robots_state']:
            robot = VirtualRobot.VirtualRobot(
                self.board[robot_state['pos'][0],
                           robot_state['pos'][1]], robot_state['index'],
                robot_state['color'], robot_state['mail'],
                robot_state['count_mail'], robot_state['battery'])
            self.robots[robot.color].append(robot)
        for green_cell, mail_number in zip(self.board.green_cells,
                                           state['generated_mails']):
            green_cell.mail = mail_number

    def sum_count_mail(self, color: str) -> int:
        return sum([robot.count_mail for robot in self.robots[color]])

    def update(self, state: dict[str,
                                 list[dict[str, Any]] | list[int]]) -> None:
        for robot_state in state['robots_state']:
            robot: VirtualRobot.VirtualRobot = self.robots[
                robot_state['color']][robot_state['index'] - 1]
            robot.pos.robot = None
            robot.pos = self.board[robot_state['pos'][0],
                                   robot_state['pos'][1]]
            robot.pos.robot = robot
            robot.mail = robot_state['mail']
            robot.count_mail = robot_state['count_mail']
            robot.battery = robot_state['battery']
        for green_cell, mail_number in zip(self.board.green_cells,
                                           state['generated_mails']):
            green_cell.mail = mail_number

    def reset(self, state: dict[str,
                                list[dict[str, Any]] | list[int]]) -> None:
        self.board.reset()
        self.robots = {}
        for robot_state in state['robots_state']:
            self.robots[robot_state['color']] = []
        for robot_state in state['robots_state']:
            robot = VirtualRobot.VirtualRobot(
                self.board[robot_state['pos'][0],
                           robot_state['pos'][1]], robot_state['index'],
                robot_state['color'], robot_state['mail'],
                robot_state['count_mail'], robot_state['battery'])
            self.robots[robot.color].append(robot)
        for green_cell, mail_number in zip(self.board.green_cells,
                                           state['generated_mails']):
            green_cell.mail = mail_number
