"""
Base class for our game
"""
import random
import os
import logging as log
from typing import Any

import pygame
import numpy as np
import pettingzoo
import gymnasium
from gymnasium import spaces
from pettingzoo import utils

from src.game import game_components
from src.game.consts import *
from src.agents.base_agent import BaseAgent
pygame.init()

class Game(gymnasium.Env, pettingzoo.AECEnv):

    """
    A class representing our game. The game can be configured with difference parameters.
    """

    metadata = {"render_modes": ["human"], "name": "robotic_board_game", "is_parallelizable": False, "render_fps": 20}

    def __init__(self, 
                 colors_map: str, 
                 targets_map: str,
                 required_mail: int,
                 robot_colors: list[str],
                 num_robots_per_player: int = 1, 
                 with_battery: bool = False,
                 random_num_steps = False,
                 max_step: int = 500,
                 render_mode: str|None = None,
                 log_to_file: bool = False) -> None:
        
        super().__init__()
        self.game_clock = game_components.Clock()
        self.robot_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.mail_sprites: pygame.sprite.Group = pygame.sprite.Group()

        self.board = game_components.Board(colors_map=colors_map, targets_map=targets_map)
        self.required_mail = required_mail
        self.robot_colors = robot_colors
        self.max_step = max_step
        self.num_robots_per_player = num_robots_per_player
        self.num_robots = num_robots_per_player * len(robot_colors)
        self.with_battery = with_battery
        self.random_num_steps = random_num_steps
        self.steps_to_change_turn = random.choice(range(1, MAXIMUM_STEP_PER_TURN)) if self.random_num_steps else 1

        robot_cells_init = random.sample(self.board.white_cells,
                                         k=self.num_robots)
        robots: list[game_components.Robot] = [
                game_components.Robot(
                    robot_cells_init[num_robots_per_player * j + i],
                    i + 1, robot_color, self.mail_sprites, self.game_clock, with_battery=self.with_battery, render_mode=render_mode, log_to_file=log_to_file)
            for j, robot_color in enumerate(robot_colors)
            for i in range(num_robots_per_player)
        ]
        self.robots: dict[str, game_components.Robot] = {robot.color + str(robot.index):robot for robot in robots}

        # generate new mail in green cells
        for green_cell in self.board.green_cells:
            green_cell.generate_mail(self.mail_sprites, render_mode)

        # add all robots to sprites group
        self.robot_sprites.add([robot for robot in self.robots.values()])
        
        self.agents = [robot_name for robot_name in self.robots.keys()]
        self.possible_agents = self.agents[:]

        self.action_spaces: dict[str, spaces.Discrete] = {a: spaces.Discrete(5) for a in self.agents}
        robot_obs_size = 4 if self.with_battery else 3
        self.observation_spaces: dict[str, spaces.Dict]= {
            a: spaces.Dict(
                {
                    "observation": spaces.Box(
                        low=0, high=1, shape=(robot_obs_size*self.num_robots,), dtype=np.float32
                    ),
                    "action_mask": spaces.Box(low=0, high=1, shape=(self.action_spaces[a].n,), dtype=np.uint8),
                }
            )
            for a in self.agents
        }
        
        self.rewards = {a: 0 for a in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {a: False for a in self.agents}
        self.truncations = {a: False for a in self.agents}
        self.infos = {a: {} for a in self.agents}

        self._agent_selector = utils.agent_selector(self.agents)
        self.agent_selection = self._agent_selector.reset()

        self.num_steps = 0
        self.winner = None

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        self.log = log_to_file
        
        self.screen = None
        if self.render_mode == "human":
            # draw a background
            self.background = pygame.Surface((15*CELL_SIZE[0], 11*CELL_SIZE[1]))
            self.background.fill((255, 255, 255))
            # draw board
            for i in range(self.board.size):
                for j in range(self.board.size):
                    self.board[i, j].draw(self.background)
            # draw axes
            images_for_cell_coordinate = [
            pygame.font.SysFont(None, 48).render(str(i), True, (0, 0, 0))
            for i in range(9)
            ]
            for i in range(self.board.size):
                self.background.blit(
                    images_for_cell_coordinate[i],
                    ((i + 1) * CELL_SIZE[0] +
                    (CELL_SIZE[0] - images_for_cell_coordinate[i].get_width()) / 2,
                    (CELL_SIZE[1] - images_for_cell_coordinate[i].get_height()) / 2))
                self.background.blit(
                    images_for_cell_coordinate[i],
                    ((CELL_SIZE[0] - images_for_cell_coordinate[i].get_width()) / 2,
                    (i + 1) * CELL_SIZE[1] +
                    (CELL_SIZE[1] - images_for_cell_coordinate[i].get_height()) / 2)) 
            # draw baterry side identification for each robot
            images_for_baterry_bar = [
            pygame.font.SysFont(None, 24).render(str(i+1), True, (0, 0, 0))
            for i in range(self.num_robots_per_player)]
            for i, robot in enumerate(self.robots.values()):
                rect = pygame.Rect(
                    10*CELL_SIZE[0] + (5*CELL_SIZE[0] - (MAXIMUM_ROBOT_BATTERY+2) * CELL_BATTERY_SIZE[0])/2,
                    5*CELL_SIZE[1] + i * CELL_BATTERY_SIZE[1], 
                    CELL_BATTERY_SIZE[0],
                    CELL_BATTERY_SIZE[1])
                pygame.draw.circle(self.background, ROBOT_COLORS[robot.color], rect.center, CELL_BATTERY_SIZE[0] / 2 * 0.8, 0)
                pygame.draw.rect(self.background, (0,0,0), rect, 1)
                self.background.blit(
                    images_for_baterry_bar[robot.index - 1],
                    (rect.left +
                    (CELL_BATTERY_SIZE[0] - images_for_baterry_bar[robot.index - 1].get_width()) / 2,
                    rect.top +
                    (CELL_BATTERY_SIZE[1] - images_for_baterry_bar[robot.index - 1].get_height()) / 2))
            # draw baterry bar
            for j in range(self.num_robots):
                for i in range(MAXIMUM_ROBOT_BATTERY + 1):
                    rect = pygame.Rect(
                        10*CELL_SIZE[0] + (5*CELL_SIZE[0] - (MAXIMUM_ROBOT_BATTERY+2)*CELL_BATTERY_SIZE[0])/2 + (i+1) * CELL_BATTERY_SIZE[0],
                        5*CELL_SIZE[1] + j * CELL_BATTERY_SIZE[1], 
                        CELL_BATTERY_SIZE[0],
                        CELL_BATTERY_SIZE[1])
                    pygame.draw.rect(self.background, (0, 0, 0), rect, 1)
            # draw progress bar which show count of collected mails
            bar_background = pygame.image.load(os.path.join(os.getcwd(), 'assets', 'images', 'loading_bar_background.png'))
            bar_background =  pygame.transform.scale(bar_background, (3*CELL_SIZE[0],  CELL_SIZE[0]/2))
            bar_rect = bar_background.get_rect()
            for i,_ in enumerate(self.robot_colors):
                self.background.blit(bar_background, (10*CELL_SIZE[0]+(5*CELL_SIZE[0]-bar_rect.width)/2, CELL_SIZE[1]+i*1.5*bar_rect.height))

            # clock to tuning fps        
            self.clock = pygame.time.Clock()
    
    def sum_count_mail(self, color: str) -> int:
        return sum([robot.count_mail for robot in self.robots.values() if robot.color == color])
    
    def observe(self, agent: str) -> dict[str, np.ndarray]:
        robot_states = np.hstack([self.robots[a].observation for a in self.agents if a != agent])
        robot_states = np.hstack([self.robots[agent].observation, robot_states])

        mask = self.robots[agent].mask
        
        return {'observation': robot_states, 'action_mask': mask}
            
    def observation_space(self, agent: str) -> spaces.Dict:
        return self.observation_spaces[agent]
    
    def action_space(self, agent: str) -> spaces.Discrete:
        return self.action_spaces[agent]

    def reset(self, seed: int|None = None, options=None) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
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
                                         k=self.num_robots)
        for i, robot in enumerate(self.robots.values()):
            robot.reset(robot_cells_init[i])

        self.mail_sprites.empty()
        for green_cell in self.board.green_cells:
            green_cell.generate_mail(self.mail_sprites, self.render_mode)
            
        self.steps_to_change_turn = random.choice(range(1, MAXIMUM_STEP_PER_TURN)) if self.random_num_steps else 1
        self._agent_selector.reinit(self.agents)
        self.agent_selection = self._agent_selector.reset()

        self.num_steps = 0
        self.winner = None

        if self.render_mode == "human":
            self.render()

        return self.observe(self.agent_selection), self.infos[self.agent_selection]

    def step(self, action: int|None) -> tuple[dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
        if (
            self.terminations[self.agent_selection]
            or self.truncations[self.agent_selection]
        ):
            return self._was_dead_step(action)
        
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.rewards = {agent: 0 for agent in self.agents}

        # #r(s,a) and s'(s,a)
        acting_robot = self.robots[self.agent_selection]
        is_moved, reward = acting_robot.step(action)
        self.rewards[self.agent_selection] = reward
        self._accumulate_rewards()
        # if robot has moved, charge robots in blue cells
        # don't charge acting robot, it decides this itself in step method
        if is_moved and self.with_battery:
            for blue_cell in self.board.blue_cells:
                if blue_cell.robot and blue_cell.robot is not acting_robot:
                    blue_cell.robot.charge()

        self.num_steps += 1    

        if self.sum_count_mail(acting_robot.color) == self.required_mail:
            self.terminations = {a: True for a in self.agents}
            self.winner = acting_robot.color
            if self.log:
                log.info(f'At t={self.game_clock.now:04} Player {self.winner} win')

        self.truncations = {a: self.num_steps >= self.max_step for a in self.agents}
        
        if self.render_mode == "human":
            # for smooth movement
            for i in range(1, FRAME_PER_STEP+1):
                diff = tuple(a-b for a, b in zip(acting_robot.next_rect.topleft, acting_robot.rect.topleft))
                acting_robot.rect.topleft = tuple(a+i/FRAME_PER_STEP*b for a,b in zip(acting_robot.rect.topleft, diff))
                if acting_robot.mail:
                    acting_robot.mail.rect.topleft = acting_robot.rect.topleft
                self.render()
        
        self.steps_to_change_turn -= 1
        if self.steps_to_change_turn == 0:
            self.agent_selection = self._agent_selector.next() 
            self.steps_to_change_turn = random.choice(range(1, MAXIMUM_STEP_PER_TURN)) if self.random_num_steps else 1
            # return previous agent's observation as next observation if game changes turn
            return (
                self.observe(self.previous_agent),
                self._cumulative_rewards[self.previous_agent],
                self.terminations[self.agent_selection],
                self.truncations[self.agent_selection],
                {'transition_belongs_agent': self.agents.index(self.previous_agent)},
            )
        # return current agent's observation as next observation if game doesn't changes turn
        return (
            self.observe(self.agent_selection),
            self._cumulative_rewards[self.agent_selection],
            self.terminations[self.agent_selection],
            self.truncations[self.agent_selection],
            {'transition_belongs_agent': self.agents.index(self.agent_selection)},
            )
    
    @property
    def previous_agent(self):
        index = self.agents.index(self.agent_selection)
        if index == 0: 
            return self.agents[-1]
        return self.agents[index-1]

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

        for i, robot in enumerate(self.robots.values()):
            pygame.draw.circle(
                self.screen, ROBOT_COLORS[robot.color],
                (10*CELL_SIZE[0] + (5*CELL_SIZE[0] - (MAXIMUM_ROBOT_BATTERY+2)*CELL_BATTERY_SIZE[0])/2 + (robot.battery + 1.5) * CELL_BATTERY_SIZE[0],
                5*CELL_SIZE[1] + (i + 0.5) * CELL_BATTERY_SIZE[1]),
                CELL_BATTERY_SIZE[0] / 2 * 0.8, 0)
            
        acting_robot = self.robots[self.agent_selection]
        pygame.draw.rect(self.screen, ROBOT_COLORS[acting_robot.color], acting_robot.rect, 3)
        for i,color in enumerate(self.robot_colors):
            pygame.draw.rect(self.screen, ROBOT_COLORS[color], (11*CELL_SIZE[0]+3, CELL_SIZE[1]+i*1.5*CELL_SIZE[1]/2+3, \
                                                             (3*CELL_SIZE[0]-6)*self.sum_count_mail(color)/self.required_mail, CELL_SIZE[1]/2-6))
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

    def run(self, agents: list[BaseAgent]) -> tuple[str | None, int]:
        
        assert len(agents) <= len(self.agents)
        self.reset()
        num_robots_for_people = len(self.agents) - len(agents)
        if num_robots_for_people > 0 and self.render_mode is None:
            raise ValueError("Person-player can't play without rendering animation")
        agents: dict[str, BaseAgent] = {name: a for name, a in zip(self.agents[num_robots_for_people:], agents)}

        running = True
        while running and not self.terminations[self.agent_selection] and not self.truncations[self.agent_selection]:
            # Human behaviors
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()
                    if event.key == pygame.K_SPACE:
                        if not any(self.robots[self.agent_selection].mask) or self.robots[self.agent_selection].is_legal_move(game_components.Action.DO_NOTHING):
                            self.step(game_components.Action.DO_NOTHING)
                    if event.key == pygame.K_UP:
                        if not any(self.robots[self.agent_selection].mask) or self.robots[self.agent_selection].is_legal_move(game_components.Action.GO_AHEAD):
                            self.step(game_components.Action.GO_AHEAD)
                    if event.key == pygame.K_DOWN:
                        if not any(self.robots[self.agent_selection].mask) or self.robots[self.agent_selection].is_legal_move(game_components.Action.GO_BACK):
                            self.step(game_components.Action.GO_BACK)
                    if event.key == pygame.K_RIGHT:
                        if not any(self.robots[self.agent_selection].mask) or self.robots[self.agent_selection].is_legal_move(game_components.Action.TURN_RIGHT):
                            self.step(game_components.Action.TURN_RIGHT)
                    if event.key == pygame.K_LEFT:
                        if not any(self.robots[self.agent_selection].mask) or self.robots[self.agent_selection].is_legal_move(game_components.Action.TURN_LEFT):
                            self.step(game_components.Action.TURN_LEFT)

            if self.agents.index(self.agent_selection) - num_robots_for_people >= 0:
                obs = self.observe(self.agent_selection)
                action = agents[self.agent_selection].get_action(obs)  
                self.step(action)
            else:
                if self.render_mode == "human":
                    self.render()

        return self.winner, self.game_clock.now