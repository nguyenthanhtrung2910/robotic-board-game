from __future__ import annotations
from typing import Any, Callable
from collections import Counter
import warnings
import time

import numpy as np
import torch
from tianshou.policy import DQNPolicy, C51Policy
from tianshou.utils.net.discrete import NoisyLinear
from tianshou.data import Batch, PrioritizedVectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.policy.modelfree.dqn import TDQNTrainingStats
from tianshou.policy.modelfree.c51 import TC51TrainingStats
from tianshou.data.types import RolloutBatchProtocol
from tianshou.utils.torch_utils import policy_within_training_step, torch_train_mode

from src.agents.base_agent import BaseAgent

class NoisyDQNPolicy(DQNPolicy[TDQNTrainingStats]):
    """
    DQN using NoisyLinear.
    """
    def learn(self, batch: RolloutBatchProtocol, *args: Any, **kwargs: Any) -> TDQNTrainingStats:
        for module in self.model.modules():
            if isinstance(module, NoisyLinear):
                module.sample()
        if self._target:
            for module in self.model.modules():
                if isinstance(module, NoisyLinear):
                    module.sample()
        return super().learn(batch, *args, **kwargs)
    
class RainbowPolicy(C51Policy[TC51TrainingStats]):
    """
    Rainbow.
    """
    def learn(self, batch: RolloutBatchProtocol, *args: Any, **kwargs: Any) -> TC51TrainingStats:
        for module in self.model.modules():
            if isinstance(module, NoisyLinear):
                module.sample()
        if self._target:
            for module in self.model.modules():
                if isinstance(module, NoisyLinear):
                    module.sample()
        return super().learn(batch, *args, **kwargs)
    
class RLAgent(BaseAgent):
    def __init__(
            self,
            train_env: DummyVectorEnv,
            test_env: DummyVectorEnv,
            policy: DQNPolicy,
            memory: PrioritizedVectorReplayBuffer|None,
            
            batch_size: int = 64,
            steps_per_update: int = 32,
            episodes_per_train: int = 5000,
            episodes_per_test: int = 8,
            test_freq: int = 100,

            train_fn: Callable[[int, int], None]|None = None,
            test_fn: Callable[[int, int], None]|None = None,
            save_best_fn: Callable[[int], None]|None = None,
            save_last_fn: Callable[[], None]|None = None,
            stop_fn: Callable[[float], bool]|None = None,
            reward_metric: Callable[[np.ndarray], float]|None = None,

    ):
        assert episodes_per_train > 0, 'Training must be with positive number of episodes.'
        assert episodes_per_test > 0, 'Testing must be with positive number of episodes.'
        assert steps_per_update > 0, 'Net will not be updated.'

        self.train_env = train_env
        self.test_env = test_env
        self.policy = policy
        self.memory = memory

        self.batch_size = batch_size
        self.steps_per_update = steps_per_update
        self.episodes_per_train = episodes_per_train
        self.episodes_per_test = episodes_per_test
        self.test_freq = test_freq
        self.train_fn = train_fn
        self.test_fn = test_fn
        self.save_best_fn = save_best_fn
        self.save_last_fn = save_last_fn
        self.stop_fn = stop_fn
        self.reward_metric = reward_metric

        self.num_agents = train_env.get_env_attr('num_robots', id = 0)[0]
        self.max_env_step = train_env.get_env_attr('max_step', id = 0)[0]

        # policy should be always in eval mode to inference action
        # training mode is turned on only within context manager
        self.policy.eval()

    def train(self, reset_memory: bool = True) -> list[float]:
        """
        E - number of enviroments
        B - collected batch size
        O - observation-vector size
        """
        if not self.save_best_fn and not self.save_last_fn:
            warnings.warn("No saving function is provided. \
                           Last model is saved in default checkpoint: 'default_last_checkpoint.pth'.", UserWarning)
        num_envs = self.train_env.env_num
        num_collected_steps = 0
        num_collected_episodes = 0
        last_num_collected_steps = num_collected_steps
        last_num_collected_episodes = num_collected_episodes
        rewards = []
        start = time.time()
        while num_collected_episodes < self.episodes_per_train:
            all_dones_e = np.zeros(num_envs, dtype=np.bool_)
            all_observations_e, _ = self.train_env.reset()
            if self.train_fn:
                self.train_fn(num_collected_episodes, num_collected_steps)
            while not all(all_dones_e):
                # ids of envs that hasn't done
                ids_b = np.where(all_dones_e == False)[0]

                # policy generate action from envs that hasn't done
                obs_b_o = np.array([obs['observation'] for obs in all_observations_e[ids_b]])
                action_mask_b = np.array([obs['action_mask'] for obs in all_observations_e[ids_b]])
                batch_obs = Batch(obs=Batch(obs=obs_b_o, mask=action_mask_b), info=None)
                with torch.no_grad():
                    act_b = self.policy(batch_obs).act
                    act_b = self.policy.exploration_noise(act_b, batch_obs)

                # step in the envs that hasn't done
                next_obs_b, rew_b, terminated_b, truncated_b, info_b = self.train_env.step(act_b, ids_b)
                
                # add to memory
                next_obs_b_o = np.array([obs['observation'] for obs in next_obs_b])
                agent_indices_b = np.array([info['transition_belongs_agent'] for info in info_b])
                self.memory.add(
                    Batch(
                        obs=obs_b_o,
                        act=act_b,
                        rew=rew_b,
                        terminated=terminated_b,
                        truncated=truncated_b,
                        obs_next=next_obs_b_o,
                        info=info_b,
                    ),
                    buffer_ids=ids_b*self.num_agents+agent_indices_b,
                )

                num_collected_steps += ids_b.size
                # net updating
                if self.steps_per_update:
                    if ((num_collected_steps-last_num_collected_steps) >= self.steps_per_update) and (len(self.memory) >= self.batch_size):
                        with policy_within_training_step(self.policy), torch_train_mode(self.policy):
                            self.policy.update(sample_size=self.batch_size, buffer=self.memory)
                        last_num_collected_steps=num_collected_steps

                # observe new observations and dones of all envs 
                all_dones_e[ids_b] = np.logical_or(terminated_b, truncated_b)
                # all_dones_e = np.array([last()[2] or last()[3] for last in env.get_env_attr('last')])
                all_observations_e = np.array([last()[0] for last in self.train_env.get_env_attr('last')])
            
            num_collected_episodes += num_envs
            # test
            if (num_collected_episodes-last_num_collected_episodes) >= self.test_freq:
                test_stats = self.test()
                num_steps, reward_metric = test_stats['mean_num_steps'], test_stats['reward']
                if len(rewards) > 0 and reward_metric > rewards[-1] and self.save_best_fn:
                    self.save_best_fn(num_collected_episodes)
                rewards.append(reward_metric)
                print("===episode {:04d} done with epsilon {:5.3f}, number steps: {:5.1f}, reward: {:+06.2f}==="
                      .format((num_collected_episodes), self.policy.eps, num_steps, reward_metric))
                last_num_collected_episodes = num_collected_episodes

            # break if reach required reward
            if len(rewards) > 0 and self.stop_fn and self.stop_fn(rewards[-1]):
                break

        finish = time.time()      
        if self.save_last_fn:
            self.save_last_fn()
        else:
            torch.save(self.policy.state_dict(), 'default_last_checkpoint.pth')
        if reset_memory:
            self.memory.reset()

        return {'reward_metric_stats': rewards,
                'num_collected_steps': num_collected_steps,
                'num_collected_episodes': num_collected_episodes,
                'training_time': finish - start,
                }
    
    def test(self, eval_metrics: bool = False) -> tuple[float, float]:
        """
        P - number of episodes
        E - number of enviroments
        B - collected batch size
        O - observation-vector size
        A - number of agents
        """
        num_envs = self.test_env.env_num
        num_collected_steps = 0
        num_collected_episodes = 0
        rewards_p_a = np.array([]).reshape(0, self.num_agents)
        num_steps = 0
        if eval_metrics:
            time_spans = 0
            count_wins = Counter()
        while num_collected_episodes < self.episodes_per_test:
            rewards_e_a = np.zeros((num_envs, self.num_agents))
            all_dones_e = np.zeros(num_envs, dtype=np.bool_)
            all_observations_e, _ = self.test_env.reset()
            if self.test_fn:
                self.test_fn(num_collected_episodes, num_collected_steps)
            while not all(all_dones_e):
                # ids of envs that hasn't done
                ids_b = np.where(all_dones_e == False)[0]

                # policy generate action from envs that hasn't done
                obs_b_o = np.array([obs['observation'] for obs in all_observations_e[ids_b]])
                action_mask_b = np.array([obs['action_mask'] for obs in all_observations_e[ids_b]])
                batch_obs = Batch(obs=Batch(obs=obs_b_o, mask=action_mask_b), info=None)
                with torch.no_grad():
                    act_b = self.policy(batch_obs).act

                # step in the envs that hasn't done
                _, rew_b, terminated_b, truncated_b, info_b = self.test_env.step(act_b, ids_b)
                agent_indices_b = np.array([info['transition_belongs_agent'] for info in info_b])
                num_collected_steps += ids_b.size

                # observe new observations and dones of all envs 
                all_dones_e[ids_b] = np.logical_or(terminated_b, truncated_b)
                # all_dones_e = np.array([last()[2] or last()[3] for last in env.get_env_attr('last')])
                all_observations_e = np.array([last()[0] for last in self.test_env.get_env_attr('last')])
                rewards_e_a[ids_b, agent_indices_b] += rew_b

            num_collected_episodes += num_envs
            rewards_p_a = np.concatenate((rewards_p_a, rewards_e_a), axis=0)
            num_steps += sum(self.test_env.get_env_attr('num_steps'))
            if eval_metrics:
                time_spans += sum([clock.now for clock in self.test_env.get_env_attr('game_clock')])
                count_wins.update(self.test_env.get_env_attr('winner'))

        if self.reward_metric:
            reward = self.reward_metric(rewards_p_a)  
        else:
            reward = rewards_p_a.max(axis=-1).mean()  

        test_stats = {
            'reward': reward,
            'mean_num_steps': num_steps/num_collected_episodes,
            'num_collected_steps': num_collected_steps,
            'num_collected_episodes': num_collected_episodes,
        }
        if eval_metrics:
            test_stats.update({'time_spans': time_spans/num_collected_episodes, 'count_wins': dict(count_wins)})

        return test_stats
    
    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        with torch.no_grad():
            act = self.policy(Batch(obs=Batch(obs=obs['observation'].reshape(1, -1), 
                                              mask=obs['action_mask'].reshape(1,-1)), info=[])).act[0]
        return act
