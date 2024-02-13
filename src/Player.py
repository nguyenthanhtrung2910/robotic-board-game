from src.Robot import Robot
import pygame
class Player:
    def __init__(self, robot_cells_init, color, sprites_group, board) -> None:
        self.robots = [Robot(robot_cells_init[i], i+1, color, sprites_group) for i in range(len(robot_cells_init))]
        self.number_robot = len(self.robots)
        self.color = color
        self.chosen_robot = self.robots[0]
    
    @property
    def count_mail(self):
        return sum([robot.count_mail for robot in self.robots])
    
    def move(self, board):
        keys = pygame.key.get_pressed() 
        if keys[pygame.K_1] and self.number_robot >= 1:
            self.chosen_robot = self.robots[0]

        if keys[pygame.K_2] and self.number_robot >= 2:
            self.chosen_robot = self.robots[1]

        if keys[pygame.K_3] and self.number_robot >= 3:
            self.chosen_robot = self.robots[2]

        if keys[pygame.K_4] and self.number_robot >= 4:
            self.chosen_robot = self.robots[3]

        if keys[pygame.K_5] and self.number_robot >= 5:
            self.chosen_robot = self.robots[4]

        if keys[pygame.K_UP]:
            if self.chosen_robot.move_up():
                for blue_cell in board.blue_cells:
                    if blue_cell.robot:
                        if blue_cell.robot is not self.chosen_robot:
                            blue_cell.robot.charge() 

        if keys[pygame.K_DOWN]:
            if self.chosen_robot.move_down():
                for blue_cell in board.blue_cells:
                    if blue_cell.robot:
                        if blue_cell.robot is not self.chosen_robot:
                            blue_cell.robot.charge() 

        if keys[pygame.K_RIGHT]:
            if self.chosen_robot.move_right():
                for blue_cell in board.blue_cells:
                    if blue_cell.robot:
                        if blue_cell.robot is not self.chosen_robot:
                            blue_cell.robot.charge() 

        if keys[pygame.K_LEFT]:
            if self.chosen_robot.move_left():
                for blue_cell in board.blue_cells:
                    if blue_cell.robot:
                        if blue_cell.robot is not self.chosen_robot:
                            blue_cell.robot.charge() 