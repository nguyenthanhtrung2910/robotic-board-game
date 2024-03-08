import random
import logging as log

from Agents.BoardSimulator import BoardSimulator
from Agents.CellSimulator import CellSimulator
from Agents.RobotSimulator import RobotSimulator
from Agents.GameSimulator import GameSimulator

from Game.consts import *

class DefaultAgent:
    
    def __init__(self, color:str, board: BoardSimulator, required_mail: int, state) -> None:

        self.color = color
        self.simulator = GameSimulator(board, required_mail, state)
        self.dests = []
        for robot in self.simulator.robots[self.color]:
            self.dests.append(robot.get_destination(board))

    def get_action_for_one_robot(self, robot: RobotSimulator, board: BoardSimulator):
            if robot.is_charged:
                if robot.battery < 70:
                    return self.color+str(robot.index)+'s'

            if robot.pos is self.dests[robot.index-1]:
                self.dests[robot.index-1] = robot.get_destination(board)
            
            # when many other robot wait for queue to destination, go to other destination or don't move
            # we want avoid draw when all players don't want to move
                    
            if self.dests[robot.index-1].is_blocked and robot.pos not in self.dests[robot.index-1].neighbors:
                if self.dests[robot.index-1].color == 'y':
                    return self.color+str(robot.index)+'s'
                if self.dests[robot.index-1].color == 'b':
                    if all([cell.is_blocked for cell in board.blue_cells]):
                        return self.color+str(robot.index)+'s'
                    self.dests[robot.index-1] = robot.get_destination(board, [cell for cell in board.blue_cells if cell.is_blocked])
                if self.dests[robot.index-1].color == 'gr':
                    if all([cell.is_blocked for cell in board.green_cells]):
                        return self.color+str(robot.index)+'s'
                    self.dests[robot.index-1] = robot.get_destination(board, [cell for cell in board.green_cells if cell.is_blocked])

            #build the path
            path = board.a_star_search(robot.pos, self.dests[robot.index -1])
            
            if len(path) != 0:
                next = path[0]
                
                #get the action
                if next is robot.pos.front:
                    action =  self.color+str(robot.index)+'u'
                if next is robot.pos.back:
                    action = self.color+str(robot.index)+'d'
                if next is robot.pos.left:
                    action = self.color+str(robot.index)+'l'
                if next is robot.pos.right:
                    action = self.color+str(robot.index)+'r'
                
                #simulation
                if not next.robot:                 
                    robot.pos.robot = None
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
            
            return self.color+str(robot.index)+'s'

    def policy(self, state):
        #update the game state for simulator
        self.simulator.update(state)
         
        #simulation
        action = [self.get_action_for_one_robot(robot, self.simulator.board) for robot in self.simulator.robots[self.color]]

        return action
    
    def reset(self, state):
        self.simulator.reset(state)
        for robot in self.simulator.robots[self.color]:
            self.dests.append(robot.get_destination(self.simulator.board))
