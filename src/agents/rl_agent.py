from __future__ import annotations
from typing import Any, Callable
from collections import Counter
import warnings
import time

import numpy as np
import torch
from torch import nn
from tianshou.policy import DQNPolicy, C51Policy
from tianshou.utils.net.discrete import NoisyLinear
from tianshou.data import Batch, PrioritizedVectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.policy.modelfree.dqn import TDQNTrainingStats
from tianshou.policy.modelfree.c51 import TC51TrainingStats
from tianshou.data.types import RolloutBatchProtocol
from tianshou.utils.torch_utils import policy_within_training_step, torch_train_mode

from src.agents.base_agent import BaseAgent
from src.game.robotic_board_game import Game

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
            env_args: dict[str, Any],
            model: type[nn.Module],
            model_args: dict[str, Any],
            policy: type[DQNPolicy],
            policy_args: dict[str, Any],
            memory_args: dict[str, Any],
            
            num_train_envs: int = 16,
            num_test_envs: int = 8,
            batch_size: int = 64,
            lr: float = 0.0001,
            steps_per_update: int = 32,
            episodes_per_train: int = 5000,
            episodes_per_test: int = 8,
            test_freq: int = 100,

            max_eps: float = 1.0,
            min_eps: float = 0.05,
            eps_rate: float = 0.9994,
            max_beta: float = 1.0,
            min_beta: float = 0.4,
            beta_rate: float = 0.0015,
            episode_to_save: int = 0,
            reward_to_stop: float = 1000,
            best_ckpt:  str|None = None,
            last_ckpt: str|None = None,
            trained_ckpt: str|None = None,

            train_fn: Callable[[int, int], None]|None = None,
            test_fn: Callable[[int, int], None]|None = None,
            save_best_fn: Callable[[int], None]|None = None,
            save_last_fn: Callable[[], None]|None = None,
            stop_fn: Callable[[float], bool]|None = None,
            reward_metric: Callable[[np.ndarray], float]|None = None,

    ):
        assert episodes_per_train > 0, 'Training must be with positive number of episodes.'
        assert episodes_per_test > 0, 'Testing must be with positive number of episodes.'

        env_args.update({
            'render_mode': None,
            'log_to_file': False,
        })
        def make_env():
            return Game(**env_args)
        self.train_env = DummyVectorEnv([make_env for _ in range(num_train_envs)])
        self.test_env = DummyVectorEnv([make_env for _ in range(num_test_envs)])
        test_env = make_env()

        model_args.update({
            'state_shape': test_env.observation_space(test_env.agent_selection)['observation'].shape,
            'action_shape': test_env.action_space(test_env.agent_selection).n,
            'device': "cuda" if torch.cuda.is_available() else "cpu",
        })
        net = model(**model_args)
        policy_args.update({
            'model': net,
            'optim': torch.optim.Adam(net.parameters(), lr=lr),
            'action_space': test_env.action_space(test_env.agent_selection),
            'lr_scheduler': None,
        })
        self.policy = policy(**policy_args)

        memory_args.update({
            'buffer_num': self.train_env.env_num*test_env.num_robots,
        })
        self.memory = PrioritizedVectorReplayBuffer(**memory_args)

        self.batch_size = batch_size
        self.steps_per_update = steps_per_update
        self.episodes_per_train = episodes_per_train
        self.episodes_per_test = episodes_per_test
        self.test_freq = test_freq
        self.max_eps = max_eps
        self.min_eps = min_eps
        self.eps_rate = eps_rate
        self.max_beta = max_beta
        self.min_beta = min_beta
        self.beta_rate = beta_rate
        self.best_ckpt = best_ckpt
        self.last_ckpt = last_ckpt
        self.episode_to_save = episode_to_save
        self.reward_to_stop = reward_to_stop
        self.train_fn = train_fn
        self.test_fn = test_fn
        self.save_best_fn = save_best_fn
        self.save_last_fn = save_last_fn
        self.stop_fn = stop_fn
        self.reward_metric = reward_metric

        self.num_agents = test_env.num_robots

        # policy should be always in eval mode to inference action
        # training mode is turned on only within context manager
        self.policy.eval()
        if trained_ckpt is not None:
            self.policy.load_state_dict(torch.load(trained_ckpt, 
                                              weights_only=True, 
                                              map_location=torch.device(self.policy.model.device)))

    def train(self, reset_memory: bool = True) -> list[float]:
        """
        E - number of enviroments
        B - collected batch size
        O - observation-vector size
        """
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
            else:
                self.policy.set_eps(np.maximum(self.max_eps*self.eps_rate**num_collected_episodes, self.min_eps))
                self.memory.set_beta(self.max_beta + (self.min_beta - self.max_beta) * np.exp(-self.beta_rate * num_collected_episodes))
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
                if len(rewards) > 0 and reward_metric > rewards[-1]:
                    if self.save_best_fn:
                        self.save_best_fn(num_collected_episodes)
                    elif num_collected_episodes >= self.episode_to_save and self.best_ckpt:
                        torch.save(self.policy.state_dict(), self.best_ckpt)
                rewards.append(reward_metric)
                print("===episode {:04d} done with epsilon {:5.3f}, number steps: {:5.1f}, reward: {:+06.2f}==="
                      .format((num_collected_episodes), self.policy.eps, num_steps, reward_metric))
                last_num_collected_episodes = num_collected_episodes

            # break if reach required reward
            if len(rewards) > 0:
                if self.stop_fn and self.stop_fn(num_collected_episodes):
                    break
                elif rewards[-1] > self.reward_to_stop:
                    break
        finish = time.time()      
        if self.save_last_fn:
            self.save_last_fn()
        elif self.last_ckpt:
            torch.save(self.policy.state_dict(), self.last_ckpt)
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
