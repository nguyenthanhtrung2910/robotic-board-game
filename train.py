from typing import Any, Callable
import argparse

import pygame
import numpy as np
import torch
from torch import nn
from tianshou.policy import DQNPolicy
from tianshou.utils.net.common import Net
from tianshou.data import Batch, PrioritizedVectorReplayBuffer
from tianshou.utils.torch_utils import policy_within_training_step, torch_train_mode

from src.game import robotic_board_game

class DQNTrainer:
    def __init__(self,
                 env: robotic_board_game.Game, 
                 net_params: dict[str, Any] = None, 
                 policy_params: dict[str, Any] = None, 
                 replaybuffer_params: dict[str, Any] = None,
                 learning_rate: float = 0.0001,
                 batch_size: int = 64,
                 steps_per_update: int = 8,
                 max_episodes: int = 5000,
                 max_eps: int = 1.0,
                 eps_schedule: Callable[[int], float] = None,
                 beta_schedule: Callable[[int], float] = None,
                 ):
        self.env = env
        if not replaybuffer_params:
            replaybuffer_params = dict(
                total_size=2_400_000,
                alpha=0.6, 
                beta=0.4,
            )
        if not net_params:
            net_params = dict(
                norm_layer=nn.LayerNorm,
                dueling_param=[dict(), dict()],
                hidden_sizes=[256, 256, 128, 128, 64, 64],
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
        if not policy_params:
            policy_params = dict(
                discount_factor=0.99,
                estimation_step=20,
                target_update_freq=1,
                is_double=True,
            )
        replaybuffer_params['buffer_num'] = env.number_robots
        self.memory = PrioritizedVectorReplayBuffer(**replaybuffer_params)
        
        net_params['state_shape'] = env.observation_space(env.agent_selection)['observation'].shape,
        net_params['action_shape'] = env.action_space(env.agent_selection).n,
        net = Net(**net_params)
        optim = torch.optim.Adam(net.parameters(), lr=learning_rate)

        policy_params['model'] = net
        policy_params['optim'] = optim
        policy_params['action_space'] = env.action_space(env.agent_selection)
        self.policy = DQNPolicy(**policy_params)

        self.batch_size = batch_size
        self.steps_per_update = steps_per_update
        self.max_episodes = max_episodes
        self.max_eps = max_eps
        self.eps_schedule = eps_schedule if eps_schedule else lambda episode: np.maximum(max_eps*0.9995**episode, 0.05)
        self.beta_schedule = beta_schedule if beta_schedule else lambda episode: 1.0 + (0.4 - 1.0) * np.exp(-0.0015 * episode)

    def run(self) -> list[float]:
        rewards = []
        self.policy.set_eps(self.max_eps)
        for episode in range(self.max_episodes):
            self.env.reset()
            list_total_reward: list[float] = [0]*self.env.number_robots
            observation, cumulative_reward, terminated, truncated, _ = self.env.last()
            for step in range(self.env.max_step):
                #policy generate action
                action_mask = observation["action_mask"].reshape(1, -1)
                state = observation['observation'].reshape(1, -1)
                action = self.policy(Batch(obs=Batch(obs=state, mask=action_mask), info=[])).act
                #step in the enviroment
                self.env.step(action[0])
                observation, cumulative_reward, terminated, truncated, _ = env.last()
                #add to buffer
                next_state = self.env.observe(self.env.previous_agent)['observation'].reshape(1, -1)
                reward = self.env._cumulative_rewards[self.env.previous_agent]
                previous_agent_index = self.env.agents.index(self.env.previous_agent)
                self.memory.add(
                    Batch(
                        obs=state,
                        act=action,
                        rew=np.array([reward]),
                        terminated=np.array([terminated]),
                        truncated=np.array([truncated]),
                        obs_next=next_state,
                        info=np.array([{'player': previous_agent_index}], dtype=object),
                    ),
                    buffer_ids=[previous_agent_index],
                )
                list_total_reward[previous_agent_index] += reward
                if (step % self.steps_per_update == 0) and (len(self.memory) >= self.batch_size):
                    with policy_within_training_step(self.policy), torch_train_mode(self.policy):
                        self.policy.update(sample_size=self.batch_size, buffer=self.memory)

                if terminated or truncated:
                    number_steps = step
                    break
                if step == self.env.max_step - 1:
                    number_steps = step

            total_reward = max(list_total_reward)
            if episode % 20 == 0:
                rewards.append(total_reward)
                print(f'===episode {episode} done with epsilon: {self.policy.eps}, number steps: {number_steps}, reward: {total_reward}===')
            self.policy.set_eps(self.eps_schedule(episode))
            self.memory.set_beta(self.beta_schedule(episode))
        
        torch.save(self.policy.state_dict(), f'DuelDQN_for_{self.env.number_robots}_robots.pth')
        return rewards

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", help="chose colors map")
parser.add_argument("--target_map", help="chose targets map")
parser.add_argument(
    "--robot_colors",
    help="chose robot colors",
    nargs="+",
    choices=['r', 'b', 'o', 'gr', 'y'],
)
parser.add_argument(
    "--required_mail",
    help="chose required mail to win",
    default=6,
    type=int,
)
parser.add_argument(
    "--number_robots_per_player",
    help="chose number robots per player. It shouldn't more than 6",
    default=1,
    type=int,
    choices=[1, 2, 3, 4, 5, 6],
)
parser.add_argument(
    "--max_step",
    help="max step for enviroment",
    default=500,
    type=int,
)
args = parser.parse_args()
env = robotic_board_game.Game(
    colors_map=args.color_map,
    targets_map=args.target_map,
    agent_colors=args.robot_colors,
    required_mail=args.required_mail,
    number_robots_per_player=args.number_robots_per_player,
    render_mode=None,
    max_step=args.max_step,
    battery_considered=True,
)
trainer = DQNTrainer(env)
print(trainer.policy.model)
rewards = trainer.run()
with open(f"training_stats_for_{trainer.env.number_robots}_robots.txt", "w") as file:
    file.write(",".join([str(reward) for reward in rewards]))
