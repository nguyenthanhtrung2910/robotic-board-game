from __future__ import annotations
from typing import Any, Callable
import warnings

import numpy as np
from gymnasium import spaces
import torch
from torch import nn
from tianshou.policy import C51Policy
from tianshou.utils.net.common import Net
from tianshou.utils.net.discrete import NoisyLinear
from tianshou.data import Batch, PrioritizedVectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.utils.torch_utils import policy_within_training_step, torch_train_mode
from tianshou.policy.modelfree.c51 import TC51TrainingStats
from tianshou.data.types import RolloutBatchProtocol

from src.agents.base_agent import BaseAgent

class RainbowPolicy(C51Policy[TC51TrainingStats]):
    def learn(self, batch: RolloutBatchProtocol, *args: Any, **kwargs: Any) -> TC51TrainingStats:
        for module in self.model.modules():
            if isinstance(module, NoisyLinear):
                module.sample()
        if self._target:
            for module in self.model.modules():
                if isinstance(module, NoisyLinear):
                    module.sample()
        return super().learn(batch, *args, **kwargs)
    
class RainbowAgent(BaseAgent):
    def __init__(self,
                 observation_space: spaces.Dict,
                 action_space: spaces.Discrete,
                 replaybuffer: PrioritizedVectorReplayBuffer,
                 beta_schedule: Callable[[int], float],
                 net_params: dict[str, Any] = None, 
                 policy_params: dict[str, Any] = None,
                 using_noisy_net: bool = True, 
                 learning_rate: float = 0.0001,
                 batch_size: int = 64,
                 steps_per_update: int = 1,
                 max_episodes: int = 250,
                 max_eps: float = 1.0,
                 eps_schedule: Callable[[int], float]|None = None,
                 load_from_file: str|None = None,
                 device: str = "cuda" if torch.cuda.is_available() else "cpu",
                 ):
        
        super().__init__(observation_space, action_space)
        if not using_noisy_net and eps_schedule is None:
            raise ValueError('Required epsilon schedule if no using noisy net.')
        
        default_net_params = dict(
            hidden_sizes=[128, 256, 512, 512],
            norm_layer=nn.LayerNorm,
            device=device,
            num_atoms=101,
            softmax=True,
            dueling_param=[{}, {}],
        )
        self.using_noisy_net = using_noisy_net
        if using_noisy_net:
            default_net_params['linear_layer'] = NoisyLinear
            default_net_params['dueling_param'] = [dict(linear_layer=NoisyLinear), 
                                                   dict(linear_layer=NoisyLinear)]
        if net_params:
            for key, value in net_params.items():
                default_net_params[key] = value

        default_policy_params = dict(
            discount_factor=0.99,
            estimation_step=20,
            target_update_freq=100,
            is_double=True,
            num_atoms=101,
            v_min=0,
            v_max=20,
        )
        if policy_params:
            for key, value in policy_params.items():
                default_policy_params[key] = value

        self.memory = replaybuffer
        self.beta_schedule = beta_schedule
        #policy creation
        default_net_params['state_shape'] = self.observation_space['observation'].shape
        default_net_params['action_shape'] = self.action_space.n
        net = Net(**default_net_params)
        optim = torch.optim.Adam(net.parameters(), lr=learning_rate)
        default_policy_params['model'] = net
        default_policy_params['optim'] = optim
        default_policy_params['action_space'] = self.action_space
        self.policy = RainbowPolicy(**default_policy_params)
        #policy should be always in eval mode to inference action
        #training mode is turned on only within context manager
        self.policy.eval()

        self.batch_size = batch_size
        self.steps_per_update = steps_per_update
        self.max_episodes = max_episodes
        self.max_eps = max_eps
        self.eps_schedule = eps_schedule
        if load_from_file is not None:
            self.policy.load_state_dict(torch.load(load_from_file, weights_only=True, map_location=torch.device(device)))
            self.load_from_file = True
        else:
            self.load_from_file = False
        self.device = device

    def train(self, train_env: DummyVectorEnv, eval_env: DummyVectorEnv, reset_memory: bool = True) -> list[float]:
        num_cpu = len(train_env)
        num_robots = train_env.get_env_attr('number_robots', id = 0)[0]
        max_step = train_env.get_env_attr('max_step', id = 0)[0]
        rewards = []
        if not self.using_noisy_net:
            self.policy.set_eps(self.max_eps)
        for episode in range(self.max_episodes):
            dones = np.array([False]*num_cpu)
            all_obses, _ = train_env.reset()
            player = 0
            for step in range(max_step):
                #ids of envs that has not done
                ids = np.where(dones == False)[0]
                #policy generate action from envs that hasn't done
                obs = np.array([obs['observation'] for obs in all_obses[ids]])
                action_mask = np.array([obs['action_mask'] for obs in all_obses[ids]])
                batch_obs = Batch(obs=Batch(obs=obs, mask=action_mask), info=[])
                with torch.no_grad():
                    act = self.policy(batch_obs).act
                if not self.using_noisy_net:
                    act = self.policy.exploration_noise(act, batch_obs)    
                #step in the envs that has not done
                next_obs, rew, terminated, truncated, info = train_env.step(act, ids)
                next_obs = np.array([obs['observation'] for obs in next_obs])

                #add to memory
                self.memory.add(
                    Batch(
                        obs=obs,
                        act=act,
                        rew=rew,
                        terminated=terminated,
                        truncated=truncated,
                        obs_next=next_obs,
                        info=info,
                    ),
                    buffer_ids=num_cpu*player + ids,
                )

                #net updating
                if (step % self.steps_per_update == 0) and (len(self.memory) >= self.batch_size):
                    with policy_within_training_step(self.policy), torch_train_mode(self.policy):
                        self.policy.update(sample_size=self.batch_size, buffer=self.memory)

                #observe new observations and dones of all envs 
                dones[ids] = np.logical_or(terminated, truncated)
                # dones = np.array([last()[2] or last()[3] for last in env.get_env_attr('last')])
                all_obses = np.array([last()[0] for last in train_env.get_env_attr('last')])
                player = (player + 1)%num_robots

                #break when all envs are terminated or truncated
                if all(dones):
                    num_steps = step
                    break
                if step == max_step - 1:
                    num_steps = step

            if episode % 10 == 0:
                num_steps, total_reward = self.eval(eval_env)
                if len(rewards) > 5 and total_reward > rewards[-1]:
                    torch.save(self.policy.state_dict(), f'RainbowDQN_{num_robots}_robots_best.pth')
                rewards.append(total_reward)
                print("===episode {:04d} done with epsilon {:4.3f}, number steps: {:3d}, reward: {:04.2f}===".format(episode, self.policy.eps, num_steps, total_reward))

            if not self.using_noisy_net:
                self.policy.set_eps(self.eps_schedule(episode))
            self.memory.set_beta(self.beta_schedule(episode))
        
        torch.save(self.policy.state_dict(), f'RainbowDQN_{num_robots}_robots_last.pth')
        with open(f"training_stats_{num_robots}_robots.txt", "w") as file:
            file.write(",".join([str(reward) for reward in rewards]))
            
        if reset_memory:
            self.memory.reset()
        train_env.close()

        return rewards
    
    def eval(self, env: DummyVectorEnv) -> tuple[int, np.ndarray]:
        num_cpu = len(env)
        num_robots = env.get_env_attr('number_robots', id = 0)[0]
        max_step = env.get_env_attr('max_step', id = 0)[0]

        list_total_reward = np.zeros(num_robots*num_cpu, dtype=np.float64)
        dones = np.array([False]*num_cpu)
        all_obses, infos = env.reset()
        player = 0
        for step in range(max_step):
            #ids of envs that has not done
            ids = np.where(dones == False)[0]
            #policy generate action from envs that hasn't done
            obs = np.array([obs['observation'] for obs in all_obses[ids]])
            action_mask = np.array([obs['action_mask'] for obs in all_obses[ids]])
            with torch.no_grad():
                act = self.policy(Batch(obs=Batch(obs=obs, mask=action_mask), info=[])).act
            #step in the envs that has not done
            next_obs, rew, terminated, truncated, info = env.step(act, ids)

            #observe new observations and dones of all envs 
            list_total_reward[num_cpu*player + ids] += rew
            dones[ids] = np.logical_or(terminated, truncated)
            # dones = np.array([last()[2] or last()[3] for last in env.get_env_attr('last')])
            all_obses = np.array([last()[0] for last in env.get_env_attr('last')])
            player = (player + 1)%num_robots

            #break when all envs are terminated or truncated
            if all(dones):
                num_steps = step
                break
            if step == max_step - 1:
                num_steps = step
        reward = np.reshape(list_total_reward, (num_robots, -1)).max(axis=0).mean()
        return num_steps, reward

    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        if self.policy.training:
            raise RuntimeError("Please turn policy to eval mode before get an action")
        if not self.load_from_file:
            warnings.warn("No pre-trained model is loaded. Agent can give random action.", UserWarning)
        return self.policy(Batch(obs=Batch(obs=obs['observation'].reshape(1, -1), mask=obs['action_mask'].reshape(1,-1)), info=[])).act[0]
    
