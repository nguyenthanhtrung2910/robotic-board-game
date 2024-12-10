from __future__ import annotations
from typing import Any, Callable
from collections import Counter
import time
import os

import numpy as np
import matplotlib.pyplot as plt
from tianshou.data import Batch
from tianshou.env import DummyVectorEnv
# from tianshou.utils.torch_utils import (
#     policy_within_training_step, 
#     torch_train_mode,
#     )

from rbgame.agent.rl_agent import RLAgent
from rbgame.game.game import RoboticBoardGame

class DecentralizedTrainer:
    """
    A decentralized trainer.

    :param env_args: Arguments for enviroment.
    :param num_train_env: Number enviroments used in train phase.
    :param num_test_env: Number enviroments used in test phase.
    :param batch_size: Batch size. 
    :param update_freq: After how many steps do a policy update, now only update by steps.
    :param test_freq: After how many episodes do a test.
    :param episodes_per_train: Total number episodes of training. 
    :param episodes_per_test: Total number episodes in a test. 
    :param train_fn: A hook called after each :code:`num_train_env` episodes during training.
                     It can be used to perform custom additional operations,
                     with the signature :code:`f(num_collected_episodes: int, num_collected_steps: int) -> None`.
    :param test_fn: A hook called after each :code:`num_test_env` episodes during testing.
                    It can be used to perform custom additional operations, 
                    with the signature :code:`f(num_collected_episodes: int, num_collected_steps: int) -> None`.
    :param save_best_fn: A hook called when the reward metric get better during training.
                         with the signature :code:`f(episode_to_call: int) -> None`.
    :param save_last_fn: A hook called when training has finished.
    :param stop_fn: A hook called after each :code:`num_train_env` episodes during training 
                    with the signature :code:`f(reward_to_stop: int, episode_to_stop: int) -> bool`.
    :param reward_metric: A function with signature :code:`f(rewards: np.ndarray with shape 
                          (num_episode, agent_num)) -> a scalar np.ndarray`. We need to return a single scalar 
                          to monitor training. This function specifies what is the desired metric, 
                          e.g., the reward of agent 1 or the average reward over all agents.
    """
    def __init__(
        self,
        env_args: dict[str, Any],
        
        num_train_envs: int = 16,
        num_test_envs: int = 16,
        batch_size: int = 64,
        update_freq: int = 100,
        test_freq: int = 100,
        episodes_per_train: int = 5000,
        episodes_per_test: int = 50,
        train_fn: Callable[[int, int], None]|None = None,
        test_fn: Callable[[int, int], None]|None = None,
        save_best_fn: Callable[[int], None]|None = None,
        save_last_fn: Callable[[], None]|None = None,
        stop_fn: Callable[[float, int], bool]|None = None,
        reward_metric: Callable[[np.ndarray], float]|None = None,
        # agent stores in memory transitions of the other or not
        shared_memory: bool = True,
    ) -> None:

        env_args.update({
            'render_mode': None,
            'log_to_file': False,
            })
        def make_env():
            return RoboticBoardGame(**env_args)
        self.train_env = DummyVectorEnv([make_env for _ in range(num_train_envs)])
        self.test_env = DummyVectorEnv([make_env for _ in range(num_test_envs)])

        self.batch_size = batch_size
        self.update_freq = update_freq
        self.test_freq = test_freq
        self.episodes_per_train = episodes_per_train
        self.episodes_per_test = episodes_per_test
        self.train_fn = train_fn
        self.test_fn = test_fn 
        self.save_best_fn = save_best_fn
        self.save_last_fn = save_last_fn
        self.stop_fn = stop_fn if stop_fn else \
        lambda reward, episode: False
        self.reward_metric = reward_metric if reward_metric else \
        lambda rewards: rewards.mean()
        self.shared_memory = shared_memory

        self.num_agents = self.train_env.get_env_attr('num_agents')[0]
        self.agent_names = self.train_env.get_env_attr('agents')[0]

    def train(
            self, 
            agents: list[RLAgent], 
            learning_mask: list|np.ndarray, 
            plot: bool=True
        ) -> dict[str, Any]:
        """
        Agents play together to learn.

        :param agents: :py:class:`list` of agents, which participate in game.
        :param learning_mask: A binary vector to define which agent need to learn.
        :param plot: Plot a graph of metric evolulation and save it. 
        :return: Training statistic.
        """

        # E - number of enviroments
        # B - collected batch size
        # R - number of running envs 
        # O - observation-vector size
        assert any(learning_mask), 'We need at least one learning agent.'
        assert self.num_agents == len(agents), f'Please provide number of agents is {self.num_agents}'
        assert self.num_agents == len(learning_mask), f'Please provide learning_mask size is {self.num_agents}'
        for agent_index, agent in enumerate(agents):
            if learning_mask[agent_index]:
                assert agent.memory is not None, f'Learning agent {agent_index} must having a memory.'
                assert self.num_agents*self.train_env.env_num == agent.memory.buffer_num
        
        agents: dict[str, RLAgent] = {k: v for k, v in zip(self.agent_names, agents)}
        num_envs = self.train_env.env_num
        num_collected_steps = 0
        num_collected_episodes = 0
        num_gradient_steps = 0
        last_num_collected_steps = num_collected_steps
        last_num_collected_episodes = num_collected_episodes
        # lists to record data for plotting
        episodes = []
        rewards = []
        start = time.time()
        while num_collected_episodes < self.episodes_per_train:
            done_e = np.zeros(num_envs, dtype=np.bool_)
            obs_e, _ = self.train_env.reset()
            # train function do some stuffs at beginning of every episode 
            if self.train_fn:
                self.train_fn(num_collected_episodes, num_collected_steps)
            while not all(done_e):
                # ids and current observations of running envs
                ids_r = np.where(done_e == False)[0]
                obs_r = obs_e[ids_r]
                # current agents of these envs
                current_agents_r = np.array(self.train_env.get_env_attr('agent_selection', id = ids_r))
                for agent_index, (name, agent) in enumerate(agents.items()):
                    # indicies and of envs within running envs that have current agent is ```agent```
                    # we call such env is right env
                    env_inner_indicies_b = np.where(current_agents_r == name)[0]
                    ids_b = ids_r[env_inner_indicies_b]
                    obs_b = obs_r[env_inner_indicies_b]
                    if len(env_inner_indicies_b) == 0:
                        # skip if no env is in ```agent```'s turn
                        continue

                    # policy generate action from right envs
                    obs_b_o = np.array([obs['observation'] for obs in obs_b])
                    action_mask_b = np.array([obs['action_mask'] for obs in obs_b])
                    obs_batch_b = Batch(obs=Batch(obs=obs_b_o, mask=action_mask_b), info=None)
                    # with policy_within_training_step(agent.policy):
                    act_b = agent.infer_act(obs_batch_b, exploration_noise=True)

                    # step in the right envs
                    next_obs_b, rew_b, terminated_b, truncated_b, info_b = self.train_env.step(act_b, ids_b)
                    next_obs_b_o = np.array([obs['observation'] for obs in next_obs_b])

                    # add transitions to memories of all learning agents, only shared memory now
                    for a_i, a in enumerate(agents.values()):
                        if learning_mask[a_i]:
                            # mofify or reset data in one memory doesn't change data in the other
                            # so we don't need to create copy of data to store in next buffer
                            a.memory.add(
                                Batch(
                                    obs=obs_b_o,
                                    act=act_b,
                                    rew=rew_b,
                                    terminated=terminated_b,
                                    truncated=truncated_b,
                                    obs_next=next_obs_b_o,
                                    info=info_b,
                                ),
                                buffer_ids=ids_b*self.num_agents+agent_index,
                            )

                num_collected_steps += ids_r.size

                # policies updating
                if ((num_collected_steps-last_num_collected_steps) >= self.update_freq):
                    for agent_index, agent in enumerate(agents.values()):
                        if learning_mask[agent_index]:
                            # with policy_within_training_step(agent.policy), torch_train_mode(agent.policy):
                            agent.policy.train()
                            num_bonus_steps = num_collected_steps-last_num_collected_steps
                            num_gradient_steps += agent.policy_update_fn(self.batch_size, num_bonus_steps)
                            agent.policy.eval()
                    last_num_collected_steps=num_collected_steps

                # observe new observations and dones of all envs 
                last_e = [last() for last in self.train_env.get_env_attr('last')]
                done_e = np.array([last[2] or last[3] for last in last_e])
                obs_e = np.array([last[0] for last in last_e])

            num_collected_episodes += num_envs

            # test
            if (num_collected_episodes-last_num_collected_episodes) >= self.test_freq:
                test_stats = self.test(agents.values(), eval_metrics=False)
                num_steps, reward_metric = test_stats['mean_num_steps'], test_stats['reward']
                if len(rewards) > 0 and reward_metric > rewards[-1] and self.save_best_fn:
                    self.save_best_fn(num_collected_episodes)
                episodes.append(num_collected_episodes)
                rewards.append(reward_metric)
                print("===episode {:04d} done with number steps: {:5.1f}, reward: {:+06.2f}==="
                      .format((num_collected_episodes), num_steps, reward_metric))
                last_num_collected_episodes = num_collected_episodes
                # break if reach required reward
                if self.stop_fn(rewards[-1], num_collected_episodes):
                    break

        finish = time.time()      
        if self.save_last_fn:
            self.save_last_fn()

        if plot:
            self.plot_stats(episodes, rewards)

        return {
            'reward_metric_stats': rewards,
            'num_collected_steps': num_collected_steps,
            'num_collected_episodes': num_collected_episodes,
            'num_gradient_steps': num_gradient_steps,
            'training_time': finish - start,
            }
    
    @staticmethod
    def plot_stats(episodes: list[int], rewards: list[float]) -> None:
        fig, axes = plt.subplots(1, 1, figsize=(6, 4))
        axes.plot(np.array(episodes), np.array(rewards), marker='.', color='b', label='reward')
        axes.set_xlabel("Number of collected episodes")
        axes.set_ylabel("Reward metric")
        axes.set_title("Performance of agent through episode.")
        axes.legend()
        axes.grid()
        fig.tight_layout()
        os.makedirs(os.path.join(os.getcwd(), 'plots'), exist_ok=True)
        fig.savefig(os.path.join(os.getcwd(), 'plots', 'results.png'), dpi=150, bbox_inches="tight")

    def test(
            self, 
            agents: list[RLAgent], 
            eval_metrics: bool = False,
        ) -> dict[str, Any]:
        """
        Test trained agents.

        :param agents: :py:class:`list` of agents, which participate in game.
        :param eval_metrics: Evaluate some addition metric of game process.
        :return: Testing statistic.
        """

        # P - number of episodes
        # E - number of enviroments
        # B - collected batch size
        # R - number of running envs
        # O - observation-vector size
        # A - number of agents
        assert self.num_agents == len(agents), f'Please provide number of agents is {self.num_agents}'

        agents: dict[str, RLAgent] = {k: v for k, v in zip(self.agent_names, agents)}
        num_envs = self.test_env.env_num
        num_collected_steps = 0
        num_collected_episodes = 0
        num_finished_episodes = 0
        rewards_p_a = np.array([]).reshape(0, self.num_agents)
        if eval_metrics:
            time_spans = 0
            count_wins = Counter()
        while num_collected_episodes < self.episodes_per_test:
            rewards_e_a = np.zeros((num_envs, self.num_agents))
            done_e = np.zeros(num_envs, dtype=np.bool_)
            obs_e, _ = self.test_env.reset()
            if self.test_fn:
                self.test_fn(num_collected_episodes, num_collected_steps)
            while not all(done_e):
                # ids and current observations of running envs
                ids_r = np.where(done_e == False)[0]
                obs_r = obs_e[ids_r]
                
                # current agents of these envs
                current_agents_r = np.array(self.test_env.get_env_attr('agent_selection', id = ids_r))
                for agent_index, (name, agent) in enumerate(agents.items()):
                    # indicies of envs within running envs that have current agent is ```agent```
                    # we call such env is right env
                    env_inner_indicies_b = np.where(current_agents_r == name)[0]
                    ids_b = ids_r[env_inner_indicies_b]
                    obs_b = obs_r[env_inner_indicies_b]
                    if len(env_inner_indicies_b) == 0:
                        # skip if no env is in ```agent```'s turn
                        continue

                    # policy generate action from right envs
                    obs_b_o = np.array([obs['observation'] for obs in obs_b])
                    action_mask_b = np.array([obs['action_mask'] for obs in obs_b])
                    obs_batch_b = Batch(obs=Batch(obs=obs_b_o, mask=action_mask_b), info=None)
                    act_b = agent.infer_act(obs_batch_b, exploration_noise=False)

                    # step in the right envs
                    _, rew_b, _, _, _ = self.test_env.step(act_b, ids_b)
                    rewards_e_a[ids_b, agent_index] += rew_b

                num_collected_steps += ids_r.size

                # observe new observations and dones of all envs 
                last_e = [last() for last in self.test_env.get_env_attr('last')]
                done_e = np.array([last[2] or last[3] for last in last_e])
                obs_e = np.array([last[0] for last in last_e])

            num_collected_episodes += num_envs
            rewards_p_a = np.concatenate((rewards_p_a, rewards_e_a), axis=0)
            if eval_metrics:
                winners_e = np.array(self.test_env.get_env_attr('winner'))
                id_finished_envs =  np.where(winners_e != None)[0]
                time_spans += sum([clock.now for clock in self.test_env.get_env_attr('game_clock', id=id_finished_envs)])
                num_finished_episodes += id_finished_envs.size
                count_wins.update(winners_e)
        reward = self.reward_metric(rewards_p_a)  
        test_stats = {
            'reward': reward,
            'mean_num_steps': num_collected_steps/num_collected_episodes,
            'num_collected_steps': num_collected_steps,
            'num_collected_episodes': num_collected_episodes,
        }
        if eval_metrics:
            test_stats.update({'time_spans': time_spans/num_finished_episodes, 'count_wins': dict(count_wins)})
        return test_stats
 