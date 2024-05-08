import os
from copy import deepcopy 
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
from tianshou.trainer import offpolicy_trainer
from Game import Game
from Game import Board
max_epsilon = 1.0             
min_epsilon = 0.05            
decay_rate = 0.0005 

def get_env():
    board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
    game = Game.Game(board, 1, 1, ['r', 'b'], render_mode=None)
    game = PettingZooEnv(game)
    return game

game = get_env()
net1 = Net(
    state_shape=game.observation_space['observation'].shape,
    action_shape=game.action_space.n,
    hidden_sizes=[128, 128, 128, 128],
    device="cuda" if torch.cuda.is_available() else "cpu",
).to("cuda" if torch.cuda.is_available() else "cpu")
optim1 = torch.optim.Adam(net1.parameters(), lr=1e-3)
policy1 = DQNPolicy(
    model=net1,
    optim=optim1,
    discount_factor=0.95,
    estimation_step=3,
    target_update_freq=320,
)
# policy1.load_state_dict(torch.load('log/ttt/dqn/policy.pth'))
policy2 = RandomPolicy(action_space=game.action_space)

policy = MultiAgentPolicyManager([policy1, policy2], game)

train_envs = DummyVectorEnv([get_env for _ in range(5)])
test_envs = DummyVectorEnv([get_env for _ in range(5)])
train_collector = Collector(
    policy,
    train_envs,
    VectorReplayBuffer(20_000, len(train_envs)),
    exploration_noise=True,
)
test_collector = Collector(policy, test_envs, exploration_noise=True)
def save_best_fn(policy):
    model_save_path = os.path.join("log", "ttt", "dqn", "policy.pth")
    os.makedirs(os.path.join("log", "ttt", "dqn"), exist_ok=True)
    torch.save(policy.policies[game.agents[0]].state_dict(), model_save_path)

def stop_fn(mean_rewards):
    return mean_rewards >= 200

def train_fn(epoch, env_step):
    p = policy1
    if env_step <= 400000:
        p.set_eps(min_epsilon + (max_epsilon - min_epsilon)*np.exp(-decay_rate*epoch*10))
    else:
        p.set_eps(min_epsilon)

def test_fn(epoch, env_step):
    p = policy1
    p.set_eps(0)

def reward_metric(rews):
    return rews[:, 0]

result = offpolicy_trainer(
    policy=policy,
    train_collector=train_collector,
    test_collector=test_collector,
    max_epoch=500,
    step_per_epoch=1000,
    step_per_collect=50,
    episode_per_test=10,
    batch_size=64,
    train_fn=train_fn,
    test_fn=test_fn,
    stop_fn=stop_fn,
    save_best_fn=save_best_fn,
    update_per_step=0.1,
    test_in_train=False,
    reward_metric=reward_metric,
    )