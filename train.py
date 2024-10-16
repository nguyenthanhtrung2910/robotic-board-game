import argparse

import pygame

from src.agents.dqn_agent import DQNAgent
from src.game.robotic_board_game import Game

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
game = Game(args.color_map, 
            args.target_map, 
            required_mail=args.required_mail, 
            agent_colors=args.robot_colors,
            number_robots_per_player=args.number_robots_per_player,
            with_battery=args.with_battery,
            random_steps_per_turn=args.random_steps_per_turn,
            max_step=args.max_step,
            render_mode=None,
            )
agent = DQNAgent(game.observation_space(game.agent_selection),
                 game.action_space(game.agent_selection),
                )
print(agent.policy.model)
agent.train(game)
