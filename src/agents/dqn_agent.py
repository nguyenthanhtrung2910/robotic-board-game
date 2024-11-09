from __future__ import annotations
from typing import Any, Callable
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
            memory: PrioritizedVectorReplayBuffer,
            
            batch_size: int = 64,
            steps_per_update: int = 16,
            episodes_per_update: int = 0,
            episodes_per_train: int = 800,
            episodes_per_test: int = 1,
            test_freq: int = 10,

            train_fn: Callable[[int, int], None]|None = None,
            test_fn: Callable[[int, int], None]|None = None,
            save_best_fn: Callable[[int], None]|None = None,
            save_last_fn: Callable[[], None]|None = None,
            reward_metric: Callable[[np.ndarray], float]|None = None,
    ):
        assert episodes_per_train > 0, 'Training must be with positive number of episodes.'
        assert episodes_per_test > 0, 'Testing must be with positive number of episodes.'
        assert steps_per_update > 0 or episodes_per_update > 0, 'Net will not be updated.'

        self.train_env = train_env
        self.test_env = test_env
        self.policy = policy
        self.memory = memory

        self.batch_size = batch_size
        self.steps_per_update = steps_per_update
        self.episodes_per_update = episodes_per_update
        self.episodes_per_train = episodes_per_train
        self.episodes_per_test = episodes_per_test
        self.test_freq = test_freq
        self.train_fn = train_fn
        self.test_fn = test_fn
        self.save_best_fn = save_best_fn
        self.save_last_fn = save_last_fn
        self.reward_metric = reward_metric

        self.num_agents = train_env.get_env_attr('number_robots', id = 0)[0]
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
        num_cpus = self.train_env.env_num
        num_collected_steps = 0
        last_num_collected_steps = num_collected_steps
        rewards = []
        start = time.time()
        for episode in range(self.episodes_per_train):
            all_dones_e = np.zeros(num_cpus, dtype=np.bool_)
            all_observations_e, _ = self.train_env.reset()
            if self.train_fn:
                self.train_fn(episode, num_collected_steps)
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
                # dones = np.array([last()[2] or last()[3] for last in env.get_env_attr('last')])
                all_observations_e = np.array([last()[0] for last in self.train_env.get_env_attr('last')])
            
            if (episode+1) % self.test_freq == 0:
                num_steps, reward_metric = self.test()
                if len(rewards) > 0 and reward_metric > rewards[-1] and self.save_best_fn:
                    self.save_best_fn(episode)
                rewards.append(reward_metric)
                print("===episode {:04d} done with epsilon {:5.3f}, number steps: {:5.1f}, reward: {:+06.2f}==="
                      .format((episode+1), self.policy.eps, num_steps, reward_metric))
                
        finish = time.time()      
        if self.save_last_fn:
            self.save_last_fn()
        else:
            torch.save(self.policy.state_dict(), 'default_last_checkpoint.pth')
        if reset_memory:
            self.memory.reset()

        return {'reward_metric_stats': rewards,
                'num_collected_steps': num_collected_steps,
                'training_time': finish - start,
                }
    
    def test(self) -> tuple[float, float]:
        """
        P - number of episodes
        E - number of enviroments
        B - collected batch size
        O - observation-vector size
        A - number of agents
        """
        num_cpus = self.test_env.env_num
        num_collected_steps = 0
        all_rewards_p_e_a = np.zeros((self.episodes_per_test, num_cpus, self.num_agents))
        mean_step_through_episode = []
        for episode in range(self.episodes_per_test):
            all_dones_e = np.zeros(num_cpus, dtype=np.bool_)
            all_observations_e, _ = self.test_env.reset()
            if self.test_fn:
                self.test_fn(episode, num_collected_steps)
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
                # dones = np.array([last()[2] or last()[3] for last in env.get_env_attr('last')])
                all_observations_e = np.array([last()[0] for last in self.test_env.get_env_attr('last')])
                all_rewards_p_e_a[episode, ids_b, agent_indices_b] += rew_b

            mean_step_per_episode = np.array([num_steps for num_steps in self.test_env.get_env_attr('num_steps')]).mean()
            mean_step_through_episode.append(mean_step_per_episode)

        if self.reward_metric:
            reward = self.reward_metric(all_rewards_p_e_a)  
        else:
            reward = all_rewards_p_e_a.max(axis=-1).mean()  
        mean_step = np.array(mean_step_through_episode).mean()

        return mean_step, reward
    
    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        with torch.no_grad():
            act = self.policy(Batch(obs=Batch(obs=obs['observation'].reshape(1, -1), 
                                              mask=obs['action_mask'].reshape(1,-1)), info=[])).act[0]
        return act
