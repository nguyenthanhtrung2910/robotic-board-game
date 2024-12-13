from __future__ import annotations
from abc import abstractmethod

import numpy as np
import torch
import pygame
from tianshou.data import Batch, VectorReplayBuffer
from tianshou.policy.base import BasePolicy
# from tianshou.utils.net.discrete import NoisyLinear
# from tianshou.data.types import RolloutBatchProtocol
# from tianshou.policy.modelfree.dqn import TDQNTrainingStats, DQNPolicy
# from tianshou.policy.modelfree.c51 import TC51TrainingStats, C51Policy

from rbgame.agent.base_agent import BaseAgent

# class NoisyDQNPolicy(DQNPolicy[TDQNTrainingStats]):
#     """
#     DQN using NoisyLinear.
#     """
#     def learn(self, batch: RolloutBatchProtocol, *args: Any, **kwargs: Any) -> TDQNTrainingStats:
#         for module in self.model.modules():
#             if isinstance(module, NoisyLinear):
#                 module.sample()
#         if self._target:
#             for module in self.model.modules():
#                 if isinstance(module, NoisyLinear):
#                     module.sample()
#         return super().learn(batch, *args, **kwargs)
    
# class RainbowPolicy(C51Policy[TC51TrainingStats]):
#     """
#     Rainbow.
#     """
#     def learn(self, batch: RolloutBatchProtocol, *args: Any, **kwargs: Any) -> TC51TrainingStats:
#         for module in self.model.modules():
#             if isinstance(module, NoisyLinear):
#                 module.sample()
#         if self._target:
#             for module in self.model.modules():
#                 if isinstance(module, NoisyLinear):
#                     module.sample()
#         return super().learn(batch, *args, **kwargs)

class RLAgent(BaseAgent):
        """
        Base Reinforcement Learning agent.

        :param policy: Policy.
        :param memory: Replay Buffer.
        :param update_per_step: How many times agent samples from memory and learns per one step, using only in offpolicy algorithms.
        :param repeat_per_collect: How many times agents learns on sampled data, using only in onpolicy algorithms.
        """
        def __init__(
            self,
            policy: BasePolicy,
            memory: VectorReplayBuffer|None = None,
            update_per_step: float = 1.0,
            repeat_per_collect: float = 1000,
        ) -> None:
            
            self.policy = policy
            self.memory = memory if memory is not None else None
            self.update_per_step = update_per_step
            self.repeat_per_collect = repeat_per_collect

            # policy should be always in eval mode to inference action
            # training mode is turned on only within context manager
            self.policy.eval()
        
        def infer_act(self, obs_batch: Batch, exploration_noise: bool) -> np.ndarray:
            """
            Forward batch of observations through network.

            :param obs_batch: Batch of observations. 
            :param exploration_noise: Exploration or not.
            :return: Batch of actions.
            """
            with torch.no_grad():
                act = self.policy(obs_batch).act
                if exploration_noise:
                    act = self.policy.exploration_noise(act, obs_batch)
            return act
        
        @abstractmethod
        def policy_update_fn(self, batch_size: int, num_collected_steps: int) -> int:
            """
            Update policy.

            :param batch_size: Batch size.
            :param num_collected_step: Number collected steps.
            :return: Number gradient steps.
            """  

class OffPolicyAgent(RLAgent):
    def policy_update_fn(self, batch_size: int, num_collected_steps: int) -> int:
        """
        Update policy.
        For offpolicy algorithms, agent samples :code:`batch_size` of transitions from
        replay buffer to learn and repeats it several times.

        :param batch_size: Batch size.
        :param num_collected_step: Number collected steps.
        :return: Number gradient steps.
        """
        num_gradient_steps = round(self.update_per_step * num_collected_steps)
        if num_gradient_steps == 0:
            raise ValueError(
                f"n_gradient_steps is 0, n_collected_steps={num_collected_steps}, "
                f"update_per_step={self.update_per_step}",
            )
        for _ in range(num_gradient_steps):
            self.policy.update(sample_size=batch_size, buffer=self.memory)
        return num_gradient_steps
    
    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        mask = obs['action_mask'].reshape(1,-1)
        obs = obs['observation'].reshape(1, -1)
        with torch.no_grad():
            act = self.policy(Batch(obs=Batch(obs=obs, mask=mask), info=None)).act[0]
        return act