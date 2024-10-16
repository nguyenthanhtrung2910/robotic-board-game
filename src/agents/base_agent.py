
from __future__ import annotations
from abc import ABC, abstractmethod
from gymnasium import spaces
import numpy as np
class BaseAgent(ABC):
    def __init__(self, observation_space: spaces.Dict|None = None, action_space: spaces.Discrete|None = None):
        self.observation_space = observation_space
        self.action_space = action_space
    @abstractmethod
    def get_action(self, obs: dict[str, np.ndarray]) -> int:
        """
        Compute action from observation.
        :param obs: observation and action mask from game.
        :type obs: dict[str, numpy.array]
        """