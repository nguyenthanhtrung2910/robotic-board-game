from Agents.BoardSimulator import BoardSimulator
from Agents.CellSimulator import CellSimulator
from Agents.RobotSimulator import RobotSimulator

from Game.consts import *

class GameSimulator:

    def __init__(self, board: BoardSimulator, required_mail: int, state) -> None:

        self.board = board
        self.required_mail = required_mail
        self.robots = {}
        for robot_state in state:
            self.robots[robot_state['color']] = []
        for robot_state in state:
            robot = RobotSimulator(self.board[robot_state['pos'][0], robot_state['pos'][1]], 
                          robot_state['index'], 
                          robot_state['color'],
                          robot_state['mail'],
                          robot_state['count_mail'],
                          robot_state['battery'])
            self.robots[robot.color].append(robot)
        
    def sum_count_mail(self, color):
        return sum([robot.count_mail for robot in self.robots[color]]) 
            
    def update(self, state):
        for robot_state in state:
            robot: RobotSimulator = self.robots[robot_state['color']][robot_state['index']-1]
            robot.pos.robot = None
            robot.pos = self.board[robot_state['pos'][0], robot_state['pos'][1]]
            robot.pos.robot = robot
            robot.mail = robot_state['mail']
            robot.count_mail = robot_state['count_mail']
            robot.battery = robot_state['battery']

    def reset(self, state):
        self.board.reset()
        self.robots = {}
        for robot_state in state:
            self.robots[robot_state['color']] = []
        for robot_state in state:
            robot = RobotSimulator(self.board[robot_state['pos'][0], robot_state['pos'][1]], 
                          robot_state['index'], 
                          robot_state['color'],
                          robot_state['mail'],
                          robot_state['count_mail'],
                          robot_state['battery'])
            self.robots[robot.color].append(robot)

