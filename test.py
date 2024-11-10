import argparse
from typing import Any
from pprint import pprint

import pygame
import numpy as np
import yaml
import importlib
import torch
from tianshou.env import DummyVectorEnv
from tianshou.utils.net.common import Net
from tianshou.policy import DQNPolicy
from tianshou.data import PrioritizedVectorReplayBuffer

from src.game.robotic_board_game import Game
from src.agents.rl_agent import RLAgent
parser = argparse.ArgumentParser()
parser.add_argument(
    "--config", 
    help="path to configuration .yaml file",
    type=str,
)

args = parser.parse_args()

def set_class(config: dict[str, Any], key: str) -> None:
    class_path = config[key]
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    config[key] = cls

with open(args.config, "r") as file:
    config = yaml.safe_load(file)
try:
    set_class(config['net_config'], 'norm_layer')
    set_class(config['net_config'], 'activation')
    set_class(config['net_config'], 'linear_layer')
    set_class(config['net_config']['dueling_param'], 'norm_layer')
    set_class(config['net_config']['dueling_param'], 'activation')
    set_class(config['net_config']['dueling_param'], 'linear_layer')
except KeyError:
    pass

try:
    # enviroment
    config['env_config']['render_mode'] = None
    config['env_config']['log_to_file'] = False
    def make_env():
        return Game(**config['env_config'])
    game = make_env()
    train_env = DummyVectorEnv([make_env for _ in range(config['num_train_envs'])])
    test_env = DummyVectorEnv([make_env for _ in range(config['num_test_envs'])])

    # net
    config['net_config']['state_shape'] = game.observation_space(game.agent_selection)['observation'].shape
    config['net_config']['action_shape'] = game.action_space(game.agent_selection).n
    config['net_config']['device'] = "cuda" if torch.cuda.is_available() else "cpu"
    net = Net(**config['net_config'])

    # policy
    set_class(config, 'policy_type')
    set_class(config, 'optim_type')
    config['policy_config']['model'] = net
    config['policy_config']['optim'] = config['optim_type'](net.parameters(), config['learning_rate'])
    config['policy_config']['action_space'] = game.action_space(game.agent_selection)
    config['policy_config']['lr_scheduler'] = None
    policy: DQNPolicy = config['policy_type'](**config['policy_config'])
    assert type(config['trained_checkpoint']) is str or config['trained_checkpoint'] is None, 'Please provide legal trained_checkpoint.'
    if config['trained_checkpoint'] is not None:
        policy.load_state_dict(torch.load(config['trained_checkpoint'], weights_only=True, map_location=torch.device(config['net_config']['device'])))

    config['training_config']['train_env'] = train_env
    config['training_config']['test_env'] = test_env
    config['training_config']['policy'] = policy
    config['training_config']['memory'] = None
    config['training_config']['train_fn'] = None
    config['training_config']['test_fn'] = None
    config['training_config']['save_best_fn'] = None
    config['training_config']['save_last_fn'] = None
    config['training_config']['stop_fn'] = None
    config['training_config']['reward_metric'] = None
    agent = RLAgent(**config['training_config'])

except KeyError as e:
    print(f'No {e.args[0]} is provided.')
    exit()
eval_stats = agent.test(True)
pprint(eval_stats)

train_env.close()
test_env.close()

