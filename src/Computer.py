from src.Robot import Robot
import logging as log
class Computer:
    def __init__(self, robot_cells_init, color, board) -> None:
        self.robots = [Robot(robot_cells_init[i], i+1, color) for i in range(len(robot_cells_init))]
        for robot in self.robots:
            robot.set_destination(board)
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
                if robot.battery < 50:
                    return
                else:
                    robot.set_destination(board)

            path = board.a_star_search(robot.pos, robot.dest)
            if len(path) != 0:
                next = path[0]
                if not next.robot:                    
                    robot.pos.robot = None
                    robot.pos = next
                    robot.pos.robot = robot
                    robot.allowed_step_per_turn -= 1
                    robot.battery -= 1
                    log.info(f'{Robot.colors_map[robot.color]} robot {robot.index} go to position ({robot.pos.x},{robot.pos.y})')
                    if robot.pick_up(): robot.set_destination(board)
                    if robot.drop_off(): robot.set_destination(board) 
                    #charge robot in blue cells
                    for blue_cell in board.blue_cells:
                        if blue_cell.robot:
                            if blue_cell.robot is not robot:
                                blue_cell.robot.charge()       

    def move(self, board):
        if self.frame_count == self.number_robot*10:
            self.frame_count = 0
        if self.frame_count % 10 == 0:
            self.chosen_robot = self.robots[int(self.frame_count/10)]
        if self.frame_count % 10 == 5:
            self.move_robot(self.chosen_robot, board)
        self.frame_count += 1
