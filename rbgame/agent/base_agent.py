from __future__ import annotations
from abc import ABC, abstractmethod

import numpy as np

class BaseAgent(ABC):
    """
    Base agent. All agents should inherit this class.
    """
    @abstractmethod
    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        """
        Compute action from observation.

        :param obs: Observation and action mask from game.
        :return: Action. 
        """