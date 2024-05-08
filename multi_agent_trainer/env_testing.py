import os
from typing import Optional, Tuple
import stable_baselines3.common
import stable_baselines3.common.env_checker
from tianshou.data.batch import Batch
import gymnasium as gym
import numpy as np
import torch
import stable_baselines3
import tianshou as ts
from tianshou.data import Collector, VectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.env.pettingzoo_env import PettingZooEnv
from tianshou.policy import BasePolicy, DQNPolicy, MultiAgentPolicyManager, RandomPolicy
from tianshou.trainer import OffpolicyTrainer
from tianshou.utils.net.common import Net
from stable_baselines3 import DQN
from pettingzoo.classic import tictactoe_v3
from Game import Game
from Game import Board
from Agents import DefaultAgent, VirtualBoard

board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
game = Game.Game(board, 1, 1, ['r', 'b'], render_mode='human')
obs, reward, termination, truncation, info = game.last()
agent1 = DefaultAgent.DefaultAgent('r',VirtualBoard.VirtualBoard('csv_files/colors_map.csv', 'csv_files/targets_map.csv'),1, game.state)
agent2 = DefaultAgent.DefaultAgent('b',VirtualBoard.VirtualBoard('csv_files/colors_map.csv', 'csv_files/targets_map.csv'),1, game.state)
agent = {'r': agent1, 'b':agent2}
while not termination and not truncation:
    action = agent[game.agent_selection].policy(game.state)
    game.step(action)
    obs, reward, termination, truncation, info = game.last()
    print(game.agent_selection, obs, game._cumulative_rewards)
game.close()