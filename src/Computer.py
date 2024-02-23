from src.Robot import Robot
from src.consts import *
import logging as log
from src.Mail import Mail
class Computer:
    def __init__(self, robot_cells_init, color, sprites_group, clock, board) -> None:
        self.robots = [Robot(robot_cells_init[i], i+1, color, sprites_group, clock) for i in range(len(robot_cells_init))]
        for robot in self.robots:
            robot.set_destination(board,[])
        self.number_robot = len(self.robots)
        self.color = color
        self.chosen_robot = self.robots[0]
        self.frame_count = 0

    @property
    def count_mail(self):
        return sum([robot.count_mail for robot in self.robots])
    
    @staticmethod
    def move_robot(robot, board):
        if robot.allowed_step_per_turn and robot.battery:
            if robot.is_charged:
                if robot.battery < 70:
                    return False
                else:
                    robot.set_destination(board,[])
            
            # when many other robot wait for queue to destination, go to other destination or don't move
            # we want avoid draw when all players don't want move
                    
            if robot.dest.is_blocked and robot.pos not in robot.dest.neighbors:
                if robot.dest.color == 'y':
                    return False
                if robot.dest.color == 'b':
                    if all([cell.is_blocked for cell in board.blue_cells]):
                        return False
                    robot.set_destination(board, [cell for cell in board.blue_cells if cell.is_blocked])
                if robot.dest.color == 'gr':
                    if all([cell.is_blocked for cell in board.green_cells]):
                        return False
                    robot.set_destination(board, [cell for cell in board.green_cells if cell.is_blocked])

            path = board.a_star_search(robot.pos, robot.dest)
            if len(path) != 0:
                next = path[0]
                if not next.robot:                 
                    robot.pos.robot = None
                    robot.pos = next
                    robot.pos.robot = robot
                    robot.allowed_step_per_turn -= 1
                    robot.battery -= 1
                    # log.info(f'{Robot.colors_map[robot.color]} robot {robot.index} go to position ({robot.pos.x},{robot.pos.y})')
                    if robot.pick_up(): robot.set_destination(board,[])
                    if robot.drop_off(): robot.set_destination(board,[]) 
                    #charge robot in blue cells
                    for blue_cell in board.blue_cells:
                        if blue_cell.robot:
                            if blue_cell.robot is not robot:
                                blue_cell.robot.charge()   
                    robot.clock.up()
                    return True    
            return False

    def move(self, board):
        # if self.frame_count == self.number_robot*FRAME_PER_MOVE:
        #     self.frame_count = 0
        # if self.frame_count % FRAME_PER_MOVE == 0:
        #     self.chosen_robot = self.robots[int(self.frame_count/10)]
        # if self.frame_count % FRAME_PER_MOVE == int(FRAME_PER_MOVE/2):
        # for robot in self.robots:    
        #     self.move_robot(robot, board)
        return any([self.move_robot(robot, board) for robot in self.robots])
        # self.frame_count += 1
