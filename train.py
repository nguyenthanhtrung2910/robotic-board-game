import argparse

import pygame
import numpy as np
from tianshou.env import DummyVectorEnv
from tianshou.data import PrioritizedVectorReplayBuffer
from src.agents.dqn_agent import DQNAgent
from src.agents.rainbow_agent import RainbowAgent
from src.game.robotic_board_game import Game
#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--color_map", 
                    help="chose colors map",
                    type=str,
                    default="assets/csv_files/colors_map.csv")
parser.add_argument("--target_map", 
                    help="chose targets map",
                    type=str,
                    default="assets/csv_files/targets_map.csv")
parser.add_argument("--required_mail",
                    help="chose required mail to win",
                    default=6,
                    type=int)
parser.add_argument("--robot_colors",
                    help="chose robot colors",
                    nargs="+",
                    choices=['r', 'b', 'o', 'gr', 'y'])
parser.add_argument("--number_robots_per_player",
                    help="chose number robots per player. It shouldn't more than 6",
                    type=int,
                    default=1,
                    choices=[1, 2, 3, 4, 5, 6])
parser.add_argument("--with_battery",
                    help="battery is considered or not",
                    action='store_true')
parser.add_argument("--random_steps_per_turn",
                    help="allow ramdom number steps per turn or not",
                    action='store_true')
parser.add_argument("--max_step",
                    help="maximum game's step",
                    type=int,
                    default=500)
args = parser.parse_args()


def make_env():
    return Game(
        args.color_map, 
        args.target_map, 
        required_mail=args.required_mail, 
        agent_colors=args.robot_colors,
        number_robots_per_player=args.number_robots_per_player,
        with_battery=args.with_battery,
        random_steps_per_turn=args.random_steps_per_turn,
        max_step=args.max_step,
        render_mode=None,
        log_to_file=False,
    )
game = make_env()
env = DummyVectorEnv([make_env for _ in range(8)])
eval_env = DummyVectorEnv([make_env for _ in range(8)])
memory = PrioritizedVectorReplayBuffer(
    total_size=500*len(env)*300,
    buffer_num=len(env)*len(args.robot_colors),
    alpha=0.6,
    beta=0.4,
)
beta_schedule = lambda episode: 1.0 + (0.4 - 1.0) * np.exp(-0.04 * episode)
epison_schedule = lambda episode: np.maximum(1.0*0.99**episode, 0.05)
agent = RainbowAgent(
    game.observation_space(game.agent_selection),
    game.action_space(game.agent_selection),
    replaybuffer=memory,
    beta_schedule=beta_schedule,
    using_noisy_net=False,
    learning_rate=0.0001,
    batch_size=64,
    steps_per_update=1,
    max_episodes=300,
    eps_schedule=epison_schedule,
)
print(agent.policy.model)
agent.train(env, eval_env)
eval_env.close()

