import os

import ray
import gymnasium as gym
from gymnasium.spaces import Box, Discrete
from ray import tune
from ray.rllib.algorithms.dqn import DQNConfig
from ray.rllib.algorithms.dqn.dqn_torch_model import DQNTorchModel
from ray.rllib.env import PettingZooEnv
from ray.rllib.models import ModelCatalog
from ray.rllib.algorithms import ppo
from ray.rllib.models.torch.fcnet import FullyConnectedNetwork as TorchFC
from ray.rllib.utils.framework import try_import_torch
from ray.rllib.utils.torch_utils import FLOAT_MAX
from ray.tune.registry import register_env

import sb3_wrapper
from Game import Game
from Game import Board
board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
game = Game.Game(board, 1, 1,['r'])
game = sb3_wrapper.SB3Wrapper(game)
obs,_ = game.reset(seed=42)
game = gym.Wrapper(game)
ray.init()
algo = (DQNConfig()
        .training(train_batch_size=200,
                  model={"fcnet_hiddens":[512, 512, 256, 64],
                         "fcnet_activation": "relu"
                         }
                  )
        .environment(env=game)
        .rollouts(num_rollout_workers=3, 
                  rollout_fragment_length=30,
                  )
        .framework(framework="torch")
        .resources(num_cpus_for_local_worker=2, 
                   num_cpus_per_worker=1)
        )
result = tune.run('DQN', 
                  config=algo.to_dict(), 
                  num_samples=1, 
                  stop={"training_iteration": 1})

# checkpoint = result.get_last_checkpoint()
# checkpoint.to_directory('checkpoints')