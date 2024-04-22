import math

import numpy as np

from Agents import VirtualBoard
from Agents import VirtualRobot
from Agents import VirtualGame

from Game.consts import *


class DefaultAgent:

    def __init__(self, color: str, board: VirtualBoard.VirtualBoard,
                 required_mail: int, state) -> None:

        self.color = color
        self.simulator = VirtualGame.VirtualGame(board, required_mail, state)
        self.dests = []
        for robot in self.simulator.robots[self.color]:
            self.dests.append(robot.get_destination(board))

    def __get_action_for_one_robot(self, robot: VirtualRobot.VirtualRobot,
                                   board: VirtualBoard.VirtualBoard) -> int:
        if robot.is_charged:
            if robot.battery < 70:
                return 0

        if robot.pos is self.dests[robot.index - 1]:
            self.dests[robot.index - 1] = robot.get_destination(board)

        # when many other robot wait for queue to destination, go to other destination or don't move
        # we want avoid draw when all players don't want to move

        if self.dests[robot.index -
                      1].is_blocked and robot.pos not in self.dests[
                          robot.index - 1].neighbors:
            if self.dests[robot.index - 1].color == 'y':
                return 0
            if self.dests[robot.index - 1].color == 'b':
                if all([cell.is_blocked for cell in board.blue_cells]):
                    return 0
                self.dests[robot.index - 1] = robot.get_destination(
                    board,
                    [cell for cell in board.blue_cells if cell.is_blocked])
            if self.dests[robot.index - 1].color == 'gr':
                if all([cell.is_blocked for cell in board.green_cells]):
                    return 0
                self.dests[robot.index - 1] = robot.get_destination(
                    board,
                    [cell for cell in board.green_cells if cell.is_blocked])

        #build the path
        path = board.a_star_search(robot.pos, self.dests[robot.index - 1])

        if len(path) != 0:
            next = path[0]

            #get the action
            if next is robot.pos.front:
                action = 1
            if next is robot.pos.back:
                action = 2
            if next is robot.pos.left:
                action = 3
            if next is robot.pos.right:
                action = 4

            #simulation
            if not next.robot:
                robot.pos.robot = None
                if robot.pos.color == 'gr':
                    robot.pos.generate_mail()
                robot.pos = next
                robot.pos.robot = robot
                robot.battery -= 1
                robot.pick_up()
                robot.drop_off()

                #charge robot in blue cells
                for blue_cell in board.blue_cells:
                    if blue_cell.robot:
                        if blue_cell.robot is not robot:
                            blue_cell.robot.charge()

            return action

        return 0

    def policy(self, state) -> int:
        #update the game state for simulator
        self.simulator.update(state)

        #simulation
        action = [
            self.__get_action_for_one_robot(robot, self.simulator.board)
            for robot in self.simulator.robots[self.color]
        ] + [0]

        number_robots_per_agent = len(list(self.simulator.robots.values())[0])
        action = np.ravel_multi_index(action, [5]*number_robots_per_agent+[math.factorial(number_robots_per_agent)])
        
        return action

    def reset(self, state) -> None:
        self.simulator.reset(state)
        self.dests = []
        for robot in self.simulator.robots[self.color]:
            self.dests.append(robot.get_destination(self.simulator.board))
