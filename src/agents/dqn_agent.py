from __future__ import annotations
from typing import Any, Callable
import warnings

import numpy as np
from gymnasium import spaces
import torch
from torch import nn
from tianshou.policy import DQNPolicy
from tianshou.utils.net.common import Net
from tianshou.data import Batch, PrioritizedVectorReplayBuffer
from tianshou.utils.torch_utils import policy_within_training_step, torch_train_mode

from src.agents.base_agent import BaseAgent
from src.game.robotic_board_game import Game

class DQNAgent(BaseAgent):
    def __init__(self,
                 observation_space: spaces.Dict,
                 action_space: spaces.Discrete,
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
                 load_from_file: str|None = None,
                 ):
        super().__init__(observation_space, action_space)

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
        replaybuffer_params['buffer_num'] = int(self.observation_space['observation'].shape[0]/4)
        self.memory = PrioritizedVectorReplayBuffer(**replaybuffer_params)
        
        net_params['state_shape'] = self.observation_space['observation'].shape
        net_params['action_shape'] = self.action_space.n
        net = Net(**net_params)
        optim = torch.optim.Adam(net.parameters(), lr=learning_rate)
        policy_params['model'] = net
        policy_params['optim'] = optim
        policy_params['action_space'] = self.action_space
        self.policy = DQNPolicy(**policy_params)

        self.batch_size = batch_size
        self.steps_per_update = steps_per_update
        self.max_episodes = max_episodes
        self.max_eps = max_eps
        self.eps_schedule = eps_schedule if eps_schedule else lambda episode: np.maximum(1.0*0.9995**episode, 0.05)
        self.beta_schedule = beta_schedule if beta_schedule else lambda episode: 1.0 + (0.4 - 1.0) * np.exp(-0.0015 * episode)
        if load_from_file is not None:
            self.policy.load_state_dict(torch.load(load_from_file, weights_only=True, map_location=torch.device('cpu')))
            self.load_from_file = True
        else:
            self.load_from_file = False

    def train(self, env: Game, reset_memory: bool = True) -> list[float]:
        rewards = []
        self.policy.set_eps(self.max_eps)
        for episode in range(self.max_episodes):
            env.reset()
            list_total_reward: list[float] = [0]*env.number_robots
            observation, cumulative_reward, terminated, truncated, _ = env.last()
            for step in range(env.max_step):
                #policy generate action
                action_mask = observation["action_mask"].reshape(1, -1)
                state = observation['observation'].reshape(1, -1)
                action = self.policy(Batch(obs=Batch(obs=state, mask=action_mask), info=[])).act
                #step in the enviroment
                env.step(action[0])
                observation, cumulative_reward, terminated, truncated, _ = env.last()
                #add to buffer
                next_state = env.observe(env.previous_agent)['observation'].reshape(1, -1)
                reward = env._cumulative_rewards[env.previous_agent]
                previous_agent_index = env.agents.index(env.previous_agent)
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
                    break

            total_reward = max(list_total_reward)
            if episode % 20 == 0:
                rewards.append(total_reward)
                print(f'===episode {episode} done with epsilon: {self.policy.eps}, number steps: {env.num_steps}, reward: {total_reward}===')
            self.policy.set_eps(self.eps_schedule(episode))
            self.memory.set_beta(self.beta_schedule(episode))
        
        torch.save(self.policy.state_dict(), f'DuelDQN_for_{env.number_robots}_robots.pth')
        with open(f"training_stats_for_{env.number_robots}_robots.txt", "w") as file:
            file.write(",".join([str(reward) for reward in rewards]))
            
        if reset_memory:
            self.memory.reset()
        return rewards

    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        if self.policy.training:
            raise RuntimeError("Please turn policy to eval mode before get an action")
        if not self.load_from_file:
            warnings.warn("No pre-trained model is loaded. Agent can give random action.", UserWarning)
        return self.policy(Batch(obs=Batch(obs=obs['observation'].reshape(1, -1), mask=obs['action_mask'].reshape(1,-1)), info=[])).act[0]
    
