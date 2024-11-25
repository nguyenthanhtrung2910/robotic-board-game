from __future__ import annotations
from abc import ABC, abstractmethod

import numpy as np

class BaseAgent(ABC):
    @abstractmethod
    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        """
        Compute action from observation.
        :param obs: observation and action mask from game.
        :type obs: dict[str, numpy.array]
        """