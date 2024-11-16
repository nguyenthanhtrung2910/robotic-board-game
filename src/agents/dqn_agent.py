from __future__ import annotations
from typing import Any

import numpy as np
import torch
from torch import nn
from tianshou.policy import DQNPolicy
from tianshou.data import Batch, VectorReplayBuffer

from src.agents.base_agent import RLAgent

class DQNAgent(RLAgent):
    def __init__(
            self,
            model_class: type[nn.Module],
            model_args: dict[str, Any],
            policy_class: type[DQNPolicy],
            policy_args: dict[str, Any],
            
            memory_class: type[VectorReplayBuffer]|None = None,
            memory_args: dict[str, Any]|None = None,
            update_per_step: float = 1.0,
            learning_rate: float = 0.0001,
            trained_ckpt: str|None = None,
        ):
        model = model_class(**model_args)
        policy_args.update({
            'model': model,
            'optim': torch.optim.Adam(model.parameters(), lr=learning_rate),
            })
        super().__init__(policy_class, policy_args, memory_class, memory_args, update_per_step)
        if trained_ckpt:
            self.policy.load_state_dict(
                torch.load(
                    f=trained_ckpt, 
                    weights_only=True, 
                    map_location=torch.device(model_args.get('device', 'cpu')),
                    )
                )
    
    def policy_update_fn(self, batch_size: int, num_collected_steps: int) -> None:
        num_gradient_steps = round(self.update_per_step * num_collected_steps)
        if num_gradient_steps == 0:
            raise ValueError(
                f"n_gradient_steps is 0, n_collected_steps={num_collected_steps}, "
                f"update_per_step={self.update_per_step}",
            )
        for _ in range(num_gradient_steps):
            self.policy.update(sample_size=batch_size, buffer=self.memory)

    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        mask = obs['action_mask'].reshape(1,-1)
        obs = obs['observation'].reshape(1, -1)
        with torch.no_grad():
            act = self.policy(Batch(obs=Batch(obs=obs, mask=mask), info=None)).act[0]
        return act