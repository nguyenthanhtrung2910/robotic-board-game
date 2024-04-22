from Game import Game
from Game import Board
import wrapper
from gymnasium import spaces
import pettingzoo
import gymnasium as gym
from stable_baselines3 import A2C,PPO, DQN
import numpy as np
import supersuit as ss
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv
    
board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
game = Game.Game(board, 5, 1,['r'])
game = wrapper.SB3Wrapper(game)
obs,_ = game.reset(seed=42)
game = gym.Wrapper(game)
# model = DQN.load('dqn_agent')
# model.set_env(game)
# model.learn(total_timesteps=300000)
model = DQN("MlpPolicy", game, verbose=1, target_update_interval=250, learning_rate=0.1)
model.learn(total_timesteps=100000)
model.save("dqn_agent")
game.close()





