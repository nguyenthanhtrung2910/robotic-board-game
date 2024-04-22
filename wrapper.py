import pettingzoo

class SB3Wrapper(pettingzoo.utils.BaseWrapper):

    def reset(self, seed=None, options=None):
        """Gymnasium-like reset function which assigns obs/action spaces to be the same for each agent.

        This is required as SB3 is designed for single-agent RL and doesn't expect obs/action spaces to be functions
        """
        self.env.reset(seed, options)

        # Strip the action mask out from the observation space
        self.observation_space = self.env.observation_space(self.possible_agents[0])
        self.action_space = self.env.action_space(self.possible_agents[0])

        # Return initial observation, info (PettingZoo AEC envs do not by default)
        return self.env.observe(self.agent_selection), {}

    def step(self, action):
        """Gymnasium-like step function, returning observation, reward, termination, truncation, info."""
        self.env.step(action)
        agent = self.agent_selection
        return (
            self.observe(agent),
            self._cumulative_rewards[self.previous_agent],
            self.terminations[agent],
            self.truncations[agent],
            self.infos[agent],
        )