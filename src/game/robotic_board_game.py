"""
Base class for our game
"""
import random
import math
import logging as log
from itertools import permutations
from typing import Any

import pygame
import numpy as np
import pettingzoo
import gymnasium
from gymnasium import spaces
from pettingzoo import utils

from src.game import game_components
from src.consts import *

pygame.init()


class Game(pettingzoo.AECEnv):

    """
    A class representing our game. The game can be configured with difference parameters.
    """

    metadata = {"render_modes": ["human"], "name": "robotic_board_game", "is_parallelizable": False, "render_fps": 5}

    def __init__(self, 
                 colors_map: str, 
                 targets_map: str,
                 required_mail: int,
                 number_robots_per_agent: int,
                 agent_colors: list[str], 
                 render_mode: str|None = None,
                 battery_considered = False) -> None:
        
        super().__init__()
        self.game_clock = game_components.Clock()
        self.robot_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.mail_sprites: pygame.sprite.Group = pygame.sprite.Group()

        self.board = game_components.Board(colors_map=colors_map, targets_map=targets_map)
        self.required_mail = required_mail
        self.number_robots_per_agent = number_robots_per_agent
        self.number_robots = number_robots_per_agent * len(agent_colors)
        self.battery_considered = battery_considered
        # self.nomove_count = 0

        
        robot_cells_init = random.sample(self.board.white_cells,
                                         k=self.number_robots)
        self.robots = {
            robot_color: [
                game_components.Robot(
                    robot_cells_init[number_robots_per_agent * j + i],
                    i + 1, robot_color, self.mail_sprites, self.game_clock, render_mode=render_mode)
                for i in range(number_robots_per_agent)
            ]
            for j, robot_color in enumerate(agent_colors)
        }

        for green_cell in self.board.green_cells:
            green_cell.generate_mail(self.mail_sprites, render_mode)

        #add all robots to sprites group
        self.robot_sprites.add(
            [robot for color in self.robots for robot in self.robots[color]])
        
        self.agents = agent_colors
        self.possible_agents = self.agents[:]
        self.possible_orders_moving_robot = list(permutations(range(number_robots_per_agent)))

        self.action_spaces = {a: spaces.Discrete(5**(self.number_robots_per_agent)*math.factorial(number_robots_per_agent)) for a in self.agents}
        self.observation_spaces = {
            i: spaces.Dict(
                {
                    "observation": spaces.Box(
                        low=0, high=1, shape=(28*self.number_robots,), dtype=np.int8
                    ),
                    "action_mask": spaces.Box(low=0, high=1, shape=(self.action_spaces[i].n,), dtype=np.int8),
                }
            )
            for i in self.agents
        }
        
        self.rewards = {a: 0 for a in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {a: False for a in self.agents}
        self.truncations = {a: False for a in self.agents}
        self.infos = {a: {} for a in self.agents}

        self._agent_selector = utils.agent_selector(self.agents)
        self.agent_selection = self._agent_selector.reset()

        self.num_moves = 0
        self.winner = None

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        
        self.screen = None
        if self.render_mode == "human":
            #draw a background
            self.background = pygame.Surface((CELL_SIZE[0] * 19, CELL_SIZE[1] * 13))
            self.background.fill((255, 255, 255))
            #draw board
            for i in range(self.board.size):
                for j in range(self.board.size):
                    self.board[i, j].draw(self.background)
            #draw axes
            images_for_cell_coordinate = [
            pygame.font.SysFont(None, 48).render(str(i), True, (0, 0, 0))
            for i in range(9)
            ]
            for i in range(self.board.size):
                self.background.blit(
                    images_for_cell_coordinate[i],
                    ((i + 5) * CELL_SIZE[0] +
                    (CELL_SIZE[0] - images_for_cell_coordinate[i].get_width()) / 2,
                    (CELL_SIZE[1] - images_for_cell_coordinate[i].get_height()) / 2))
                self.background.blit(
                    images_for_cell_coordinate[i],
                    (4 * CELL_SIZE[0] +
                    (CELL_SIZE[0] - images_for_cell_coordinate[i].get_width()) / 2,
                    (i+1) * CELL_SIZE[1] +
                    (CELL_SIZE[1] - images_for_cell_coordinate[i].get_height()) / 2))
                
            #draw baterry side identification for each robot
            images_for_baterry_bar = [
            pygame.font.SysFont(None, 10).render(str(i), True, (255,255, 255))
            for i in range(self.number_robots_per_agent)]
            for j, agent in enumerate(self.agents):
                for i in range(self.number_robots_per_agent):
                    rect = pygame.Rect(
                        (19 * CELL_SIZE[0] - 101 * CELL_BATTERY_SIZE[0])/2 - CELL_BATTERY_SIZE[0],
                        11 * CELL_SIZE[1] + (j*self.number_robots_per_agent + i) * CELL_BATTERY_SIZE[1], 
                        CELL_BATTERY_SIZE[0],
                        CELL_BATTERY_SIZE[1])
                    pygame.draw.rect(self.background, COLOR2RBG[agent], rect, 0)
                    pygame.draw.rect(self.background, (0,0,0), rect, 1)
                    self.background.blit(
                        images_for_baterry_bar[i],
                        (rect.left +
                        (CELL_BATTERY_SIZE[0] - images_for_baterry_bar[i].get_width()) / 2,
                        rect.top +
                        (CELL_BATTERY_SIZE[1] - images_for_baterry_bar[i].get_height()) / 2))

            #draw baterry bar
            for j in range(self.number_robots):
                for i in range(MAXIMUM_ROBOT_BATTERY + 1):
                    rect = pygame.Rect(
                        (19 * CELL_SIZE[0] - 101 * CELL_BATTERY_SIZE[0])/2 + i * CELL_BATTERY_SIZE[0],
                        11 * CELL_SIZE[1] + j * CELL_BATTERY_SIZE[1], 
                        CELL_BATTERY_SIZE[0],
                        CELL_BATTERY_SIZE[1])
                    pygame.draw.rect(self.background, (0, 0, 0), rect, 1)
            #clock to tuning fps        
            self.clock = pygame.time.Clock()

    @property
    def state(self) -> dict[str, list[dict[str, Any]] | list[int]]:
        state = {}
        state['robots_state'] = [
            robot.state for color in self.robots
            for robot in self.robots[color]
        ]
        state['generated_mails'] = [
            cell.mail.mail_number for cell in self.board.green_cells
        ]
        return state
    
    def sum_count_mail(self, agent: str) -> int:
        return sum([robot.count_mail for robot in self.robots[agent]])
    
    def observe(self, agent: str) -> dict[str, np.ndarray]:
        robot_states = np.hstack([robot.observation for a in self.robots for robot in self.robots[a] if a != agent])
        robot_states = np.hstack((np.hstack([robot.observation for robot in self.robots[agent]]), robot_states))

        mask = self.robots[agent][0].mask
        for i in range(1, self.number_robots_per_agent):
            mask = np.outer(mask, self.robots[agent][i].mask)
        mask = np.tile(mask.flatten(), math.factorial(self.number_robots_per_agent))
        
        return {'observation':robot_states, 'action_mask':mask}
            
    def observation_space(self, agent: str) -> spaces.Space:
        return self.observation_spaces[agent]
    
    def action_space(self, agent: str) -> spaces.Space:
        return self.action_spaces[agent]

    def reset(self, seed=None, options=None) -> None:
        random.seed(seed)
        self.agents = self.possible_agents[:]
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}

        self.game_clock.reset()
        self.board.reset()
        
        robot_cells_init = random.sample(self.board.white_cells,
                                         k=self.number_robots)
        for i, agent in enumerate(self.robots):
            for j, robot in enumerate(self.robots[agent]):
                robot.reset(robot_cells_init[self.number_robots_per_agent*i+j])

        self.mail_sprites.empty()
        for green_cell in self.board.green_cells:
            green_cell.generate_mail(self.mail_sprites, self.render_mode)

        self._agent_selector.reinit(self.agents)
        self.agent_selection = self._agent_selector.reset()
        self.previous_agent = None

        self.num_moves = 0
        self.winner = None
        # self.nomove_count = 0

        if self.render_mode == "human":
            self.render()

    def step(self, action: int|None) -> None:
        if (
            self.terminations[self.agent_selection]
            or self.truncations[self.agent_selection]
        ):
            return self._was_dead_step(action)
        
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.rewards = {agent: 0 for agent in self.agents}

        action = np.unravel_index(action, [5]*self.number_robots_per_agent+[math.factorial(self.number_robots_per_agent)])
        for r in self.possible_orders_moving_robot[action[-1]]:
            acting_robot = self.robots[self.agent_selection][r]
            #r(s,a) and s'(s,a)
            is_moved, reward = acting_robot.step(action[r])
            self.rewards[self.agent_selection] = reward
            self._accumulate_rewards()
            if is_moved:
                for blue_cell in self.board.blue_cells:
                    if blue_cell.robot:
                        if blue_cell.robot is not self.robots[self.agent_selection][r]:
                            blue_cell.robot.charge()

        for robot in self.robots[self.agent_selection]:
            robot.allowed_step_per_turn = 1
            #we can consider now infinite battery
            if not self.battery_considered:
                robot.battery = MAXIMUM_ROBOT_BATTERY

        self.num_moves += 1    

        if self.sum_count_mail(self.agent_selection) == self.required_mail:
            self.terminations = {a: True for a in self.agents}
            self.winner = self.agent_selection
            log.info(f'At t={self.game_clock.now:04} Player {self.winner} win')

        self.truncations = {a: self.num_moves >= NUM_ITERS for a in self.agents}

        self.previous_agent = self.agent_selection
        self.agent_selection = self._agent_selector.next() 
        
        if self.render_mode == "human":
            self.render()

    def render(self) -> None:
        if self.render_mode is None:
            gymnasium.logger.warn(
                "You are calling render method without specifying any render mode."
            )
        elif self.render_mode == "human":
            self._render_gui()
        else:
            raise ValueError(
                f"{self.render_mode} is not a valid render mode. Available modes are: {self.metadata['render_modes']}"
            )

    def _render_gui(self) -> None:
        if self.screen is None:
            self.screen = pygame.display.set_mode(
            self.background.get_size())
            pygame.display.set_caption('Robotics Board Game')

        self.screen.blit(self.background, (0, 0))

        self.robot_sprites.draw(self.screen)
        self.mail_sprites.draw(self.screen)

        for i, color in enumerate(self.robots):
            for robot in self.robots[color]:
                pygame.draw.circle(
                    self.screen, COLOR2RBG[robot.color],
                    ((19 * CELL_SIZE[0] - 101 * CELL_BATTERY_SIZE[0])/2 + (robot.battery + 0.5) * CELL_BATTERY_SIZE[0],
                    11 * CELL_SIZE[1] + (i * self.number_robots_per_agent + robot.index - 1 + 0.5) * CELL_BATTERY_SIZE[1]),
                    CELL_BATTERY_SIZE[0] / 2 * 0.8, 0)

        self.clock.tick(self.metadata["render_fps"])
        pygame.display.update()
    
    def close(self) -> None:
        pass

    def watch(self) -> None:
        running = True
        while running :
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.render()

    def run(self, agents: list[Any]) -> tuple[str | None, int]:
        
        assert len(agents) <= len(self.agents)

        self.reset()
        for agent in agents:
            agent.reset(self.state)

        number_people = len(self.agents) - len(agents)
        agents = {c: a for c, a in zip(self.agents[number_people:], agents)}
        acting_robot = self.robots[self.agent_selection][0]
        running = True

        while running and not self.terminations[self.agent_selection] and not self.truncations[self.agent_selection]:
            #Human behavior
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    
                    if event.key == pygame.K_r:
                        self.reset()
                        for agent in agents.values():
                            agent.reset(self.state)
                        
                    if event.key == pygame.K_f:
                        # self.nomove_count += 1
                        for robot in self.robots[self.agent_selection]:
                            robot.allowed_step_per_turn = 1
                            #we can consider now infinite battery
                            if not self.battery_considered:
                                robot.battery = MAXIMUM_ROBOT_BATTERY

                        self.num_moves += 1    

                        if self.sum_count_mail(self.agent_selection) == self.required_mail:
                            self.terminations = {a: True for a in self.agents}
                            self.winner = self.agent_selection
                            log.info(f'At t={self.game_clock.now:04} Player {self.winner} win')

                        # if self.nomove_count == 3 * len(self.agents):
                        #     self.terminations = {a: True for a in self.agents}

                        self.truncations = {a: self.num_moves >= NUM_ITERS for a in self.agents}

                        self.previous_agent = self.agent_selection
                        self.agent_selection = self._agent_selector.next() 

                    if event.key == pygame.K_1 and self.number_robots_per_agent >= 1:
                        acting_robot = self.robots[self.agent_selection][0]

                    if event.key == pygame.K_2 and self.number_robots_per_agent >= 2:
                        acting_robot = self.robots[self.agent_selection][1]

                    if event.key == pygame.K_3 and self.number_robots_per_agent >= 3:
                        acting_robot = self.robots[self.agent_selection][2]

                    if event.key == pygame.K_4 and self.number_robots_per_agent >= 4:
                        acting_robot = self.robots[self.agent_selection][3]

                    if event.key == pygame.K_5 and self.number_robots_per_agent >= 5:
                        acting_robot = self.robots[self.agent_selection][4]

                    if event.key == pygame.K_UP:
                        if acting_robot.move_up():
                            # self.nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

                    if event.key == pygame.K_DOWN:
                        if acting_robot.move_down():
                            # self.nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

                    if event.key == pygame.K_RIGHT:
                        if acting_robot.move_right():
                            # self.nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

                    if event.key == pygame.K_LEFT:
                        if acting_robot.move_left():
                            # self.nomove_count = 0
                            for blue_cell in self.board.blue_cells:
                                if blue_cell.robot:
                                    if blue_cell.robot is not acting_robot:
                                        blue_cell.robot.charge()

            if self.agents.index(self.agent_selection) - number_people >= 0:
                action = agents[self.agent_selection].get_action(self.state)    
                self.step(action)
            else:
                if self.render_mode == "human":
                    self.render()

        return self.winner, self.game_clock.now