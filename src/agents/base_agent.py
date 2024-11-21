from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import gymnasium as gym
import torch
from tianshou.data import Batch
from tianshou.policy.base import BasePolicy
from tianshou.data.buffer.vecbuf import VectorReplayBuffer

class BaseAgent(ABC):
    @abstractmethod
    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        """
        Compute action from observation.
        :param obs: observation and action mask from game.
        :type obs: dict[str, numpy.array]
        """

class RLAgent(BaseAgent):
        def __init__(
            self,
            policy_class: type[BasePolicy],
            policy_args: dict[str, Any],
            
            memory_class: type[VectorReplayBuffer]|None = None,
            memory_args: dict[str, Any]|None = None,
            # how many times policy samples and learns, using only in offpolicy
            update_per_step: float = 1.0,
            # how many times policy learns on sampled data, using only in onpolicy
            repeat_per_collect: float = 1000,
        ) -> None:
            
            policy_args.update({
                'action_space': gym.spaces.Discrete(5),
            })
            self.policy = policy_class(**policy_args)
            self.memory = memory_class(**memory_args) if memory_class and memory_args else None
            self.update_per_step = update_per_step
            self.repeat_per_collect = repeat_per_collect

            # policy should be always in eval mode to inference action
            # training mode is turned on only within context manager
            self.policy.eval()
        
        def infer_act(self, obs_batch: Batch, exploration_noise: bool) -> np.ndarray:
            with torch.no_grad():
                act = self.policy(obs_batch).act
                if exploration_noise:
                    act = self.policy.exploration_noise(act, obs_batch)
            return act
        
        @abstractmethod
        def policy_update_fn(self, batch_size: int, num_collected_steps: int) -> int:
            """
            Update policy.
            """