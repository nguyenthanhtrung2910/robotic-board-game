import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import DQN

import sb3_wrapper
from Game import Game
from Game import Board


def evaluate(agent, env, n_eval_episodes):
    episode_rewards = []
    for episode in range(n_eval_episodes):
        state, _ = env.reset()
        truncation = False
        termination = False
        total_rewards_ep = 0

        while not termination and not truncation:
            action = agent.predict(state, deterministic = True)[0]
            new_state, reward, termination, truncation, _ = env.step(action)
            total_rewards_ep += reward
            state = new_state
        episode_rewards.append(total_rewards_ep)

    mean_reward = np.mean(episode_rewards)
    std_reward = np.std(episode_rewards)

    return mean_reward, std_reward
    
board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
game = Game.Game(board, 1, 1,['r'])
game = sb3_wrapper.SB3Wrapper(game)
obs,_ = game.reset(seed=42)
game = gym.Wrapper(game)

model = DQN("MlpPolicy", game, verbose=1)
model.learn(150*10000)
model.save('dqn_agent')
print(evaluate(model, game, 10))




