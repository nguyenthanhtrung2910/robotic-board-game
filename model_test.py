import stable_baselines3.common
import stable_baselines3.common.env_checker
from Game import Game
from Game import Board
from Agents import DefaultAgent,VirtualBoard
from gymnasium import spaces
import pettingzoo
import gymnasium as gym
import stable_baselines3
from stable_baselines3 import A2C, DQN
import numpy as np
import supersuit as ss
import sb3_wrapper 
from Game import Mail
import time

from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv
board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
game = Game.Game(board, 1, 1,['r'], render_mode='human')
game = sb3_wrapper.SB3Wrapper(game)
obs,_ = game.reset(seed=42)
game = gym.Wrapper(game)
# game.render()
# game.robots['r'][0].pos.robot = None
# game.robots['r'][0].pos = board[6, 1]
# game.robots['r'][0].pos.robot = game.robots['r'][0]
# robot = game.robots['r'][0]
# robot.mail = Mail.Mail(5, robot.pos)
# game.mail_sprites.add(robot.mail)
# game.render()
# _, re, _, _, _ = game.step(1)
# print(re)
# game.render()
# _, re, _, _, _ = game.step(3)
# print(re)

# stable_baselines3.common.env_checker.check_env(game)
# agent1 = DefaultAgent.DefaultAgent('r',VirtualBoard.VirtualBoard('csv_files/colors_map.csv', 'csv_files/targets_map.csv'),1, game.unwrapped.state)
# termination = False
# truncation = False
# for i in range(100):
#     if not termination or truncation:
#         action = agent1.policy(game.unwrapped.state)
#         print(action)
#         observation, reward, termination, truncation, info = game.step(action)
#         print(observation)
#         print(reward)
# game.close()

agent2 = DQN.load('dqn_agent')
obs, _ = game.reset()
ter = False
tru = False
for i in range(20):
    if not ter and not tru:
        print(obs)
        action = agent2.predict(obs, deterministic=True)[0]
        print(action)
        obs, rew,ter,tru, _ = game.step(action) 
# # print(game.unwrapped.sum_count_mail('r'), game.unwrapped.sum_count_mail('r'))