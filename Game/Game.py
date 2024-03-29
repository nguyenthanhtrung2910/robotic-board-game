import random
import logging as log
from itertools import cycle
from typing import Any
import pygame

from Game import Board
from Game import Robot
from Game import Clock
from Agents import DefaultAgent
from Game.consts import *

pygame.init()


class Game:

    images_for_cell_coordinate = [
        pygame.font.SysFont(None, 48).render(str(i), True, (0, 0, 0))
        for i in range(9)
    ]
    color_map = {
        'b': (0, 0, 255),
        'r': (255, 0, 0),
        'y': (255, 255, 0),
        'g': (0, 255, 0),
        'o': (255, 165, 0)
    }

    def __init__(self, board: Board.Board, required_mail: int,
                 number_robots_with_same_color: int,
                 robot_colors: list[str]) -> None:

        self.screen = pygame.display.set_mode(
            (CELL_SIZE[0] * 28, CELL_SIZE[1] * 11))
        pygame.display.set_caption('Robotics Board Game')
        self.game_clock = Clock.Clock()
        self.robot_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.mail_sprites: pygame.sprite.Group = pygame.sprite.Group()

        self.board = board
        self.required_mail = required_mail
        self.number_robots_with_same_color = number_robots_with_same_color
        self.cycle_robot_colors = cycle(robot_colors)
        self.number_robots = number_robots_with_same_color * len(robot_colors)

        robot_cells_init = random.sample(self.board.white_cells,
                                         k=self.number_robots)
        self.robots = {
            robot_color: [
                Robot.Robot(
                    robot_cells_init[number_robots_with_same_color * j + i],
                    i + 1, robot_color, self.mail_sprites, self.game_clock)
                for i in range(number_robots_with_same_color)
            ]
            for j, robot_color in enumerate(robot_colors)
        }

        #draw a background
        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill((255, 255, 255))
        #draw board
        for i in range(self.board.size):
            for j in range(self.board.size):
                self.board[i, j].draw(self.background)
        #draw axes
        for i in range(self.board.size):
            self.background.blit(
                self.images_for_cell_coordinate[i],
                ((i + 1) * CELL_SIZE[0] +
                 (CELL_SIZE[0] -
                  self.images_for_cell_coordinate[i].get_width()) / 2,
                 (CELL_SIZE[1] -
                  self.images_for_cell_coordinate[i].get_height()) / 2))
            self.background.blit(
                self.images_for_cell_coordinate[i],
                ((CELL_SIZE[0] -
                  self.images_for_cell_coordinate[i].get_width()) / 2,
                 (i + 1) * CELL_SIZE[1] +
                 (CELL_SIZE[1] -
                  self.images_for_cell_coordinate[i].get_height()) / 2))
        #draw baterry bar
        for j in range(self.number_robots):
            for i in range(MAXIMUM_ROBOT_BATTERY + 1):
                rect = pygame.Rect(
                    10.5 * CELL_SIZE[0] + i * CELL_BATTERY_SIZE[0],
                    (CELL_SIZE[1] * 11 -
                     CELL_BATTERY_SIZE[1] * self.number_robots) / 2 +
                    j * CELL_BATTERY_SIZE[1], CELL_BATTERY_SIZE[0],
                    CELL_BATTERY_SIZE[1])
                pygame.draw.rect(self.background, (0, 0, 0), rect, 1)

        self.robot_sprites.add(
            [robot for color in self.robots for robot in self.robots[color]])

    @property
    def state(self) -> list[dict[str, Any]]:
        return [
            robot.state for color in self.robots
            for robot in self.robots[color]
        ]

    def sum_count_mail(self, color: str) -> int:
        return sum([robot.count_mail for robot in self.robots[color]])

    def move(self, action: list[str]) -> bool:
        is_moved = [True] * len(action)
        for i, a in enumerate(action):
            is_moved[i] = self.robots[a[0]][int(a[1]) - 1].move(a[2])
            if is_moved[i]:
                for blue_cell in self.board.blue_cells:
                    if blue_cell.robot:
                        if blue_cell.robot is not self.robots[a[0]][int(a[1]) -
                                                                    1]:
                            blue_cell.robot.charge()
        return any(is_moved)

    def reset(self, number_robots_with_same_color: int,
              robot_colors: list[str]) -> None:
        self.game_clock.reset()
        self.board.reset()
        self.mail_sprites.empty()
        self.robot_sprites.empty()

        self.number_robots_with_same_color = number_robots_with_same_color
        self.cycle_robot_colors = cycle(robot_colors)
        self.number_robots = number_robots_with_same_color * len(robot_colors)

        robot_cells_init = random.sample(self.board.white_cells,
                                         k=self.number_robots)
        self.robots = {
            robot_color: [
                Robot.Robot(
                    robot_cells_init[self.number_robots_with_same_color * j +
                                     i], i + 1, robot_color, self.mail_sprites,
                    self.game_clock)
                for i in range(self.number_robots_with_same_color)
            ]
            for j, robot_color in enumerate(robot_colors)
        }

        self.robot_sprites.add(
            [robot for color in self.robots for robot in self.robots[color]])

    def run(self, agents: list[DefaultAgent.DefaultAgent]) -> tuple[str | None, int]:
        # clock = pygame.time.Clock()
        nomove_count = 0
        winner = None
        running = True
        acting_player_color = next(self.cycle_robot_colors)
        acting_robot = self.robots[acting_player_color][0]
        while running:
            self.screen.blit(self.background, (0, 0))

            #Human behavior
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_f:
                        nomove_count += 1
                        acting_player_color = next(self.cycle_robot_colors)
                        for robot in self.robots[acting_player_color]:
                            robot.allowed_step_per_turn = 1

                    if event.key == pygame.K_1 and self.number_robots_with_same_color >= 1:
                        acting_robot = self.robots[acting_player_color][0]

                    if event.key == pygame.K_2 and self.number_robots_with_same_color >= 2:
                        acting_robot = self.robots[acting_player_color][1]

                    if event.key == pygame.K_3 and self.number_robots_with_same_color >= 3:
                        acting_robot = self.robots[acting_player_color][2]

                    if event.key == pygame.K_4 and self.number_robots_with_same_color >= 4:
                        acting_robot = self.robots[acting_player_color][3]

                    if event.key == pygame.K_5 and self.number_robots_with_same_color >= 5:
                        acting_robot = self.robots[acting_player_color][4]

                    if event.key == pygame.K_UP:
                        if acting_robot.move_up():
                            nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

                    if event.key == pygame.K_DOWN:
                        if acting_robot.move_down():
                            nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

                    if event.key == pygame.K_RIGHT:
                        if acting_robot.move_right():
                            nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

                    if event.key == pygame.K_LEFT:
                        if acting_robot.move_left():
                            nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

            for agent in agents:
                if agent.color == acting_player_color:
                    action = agent.policy(self.state)
                    if not self.move(action):
                        nomove_count += 1
                    else:
                        nomove_count = 0
                    acting_player_color = next(self.cycle_robot_colors)
                    for robot in self.robots[acting_player_color]:
                        robot.allowed_step_per_turn = 1
                    break
            #game over checking
            if self.sum_count_mail(acting_player_color) == self.required_mail:
                winner = acting_player_color
                log.info(f'At t={self.game_clock.now:04} Player {winner} win')
                return winner, self.game_clock.now

            #when all player skip their turn so DRAW
            if nomove_count == 3 * len(self.robots):
                return winner, self.game_clock.now

            #draw all sprites
            self.robot_sprites.draw(self.screen)
            self.mail_sprites.draw(self.screen)

            for i, color in enumerate(self.robots):
                for robot in self.robots[color]:
                    pygame.draw.circle(
                        self.screen, self.color_map[robot.color],
                        (10.5 * CELL_SIZE[0] +
                         (robot.battery) * CELL_BATTERY_SIZE[0] +
                         CELL_BATTERY_SIZE[0] / 2,
                         (CELL_SIZE[1] * 11 -
                          CELL_BATTERY_SIZE[1] * self.number_robots) / 2 +
                         (i * self.number_robots_with_same_color +
                          robot.index - 1) * CELL_BATTERY_SIZE[1] +
                         CELL_BATTERY_SIZE[1] / 2),
                        CELL_BATTERY_SIZE[0] / 2 * 0.8, 0)

            # clock.tick(FRAME_PER_SECOND)
            pygame.display.update()

        return winner, self.game_clock.now
