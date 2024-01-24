from src.Robot import Robot

class Player:
    def __init__(self, robot_cells_init, color, board) -> None:
        self.robots = [Robot(robot_cells_init[i], i+1, color) for i in range(len(robot_cells_init))]
        self.number_robot = len(self.robots)
        self.color = color
        self.chosen_robot = self.robots[0]
    
    @property
    def count_mail(self):
        return sum([robot.count_mail for robot in self.robots])
    
    def move(self, board):
        pass