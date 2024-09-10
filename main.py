import pygame
import logging as log
import argparse

from src.game.game_components import Board
from src.game.robotic_board_game import Game
from src.a_star_agent import AStarAgent
from src.a_star_agent import Graph

pygame.init()

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", help="chose colors map")
parser.add_argument("--target_map", help="chose targets map")
parser.add_argument("--required_mail",
                    help="chose required mail to win",
                    type=int)
parser.add_argument(
    "--number_robots_with_same_color",
    help="chose number robots with same color. It shouldn't more than 6",
    default=3,
    type=int,
    choices=[1, 2, 3, 4, 5, 6, 7, 8])
parser.add_argument("--robot_colors",
                    help="chose robot colors",
                    nargs="+",
                    choices=['r', 'b', 'o', 'gr', 'y'])
parser.add_argument("--number_auto_players",
                    help="chose number auto-players",
                    type=int,
                    default=0)
args = parser.parse_args()

log.basicConfig(level=log.INFO,
                filename="events.log",
                filemode="w",
                format="%(levelname)s: %(message)s")
number_human_players = len(args.robot_colors) - args.number_auto_players
agents = []
game = Game(args.color_map, 
            args.target_map, 
            args.required_mail, 
            args.number_robots_with_same_color,
            args.robot_colors, 
            render_mode='human', 
            battery_considered=True)

for i in range(args.number_auto_players):
    agents.append(
        AStarAgent(args.robot_colors[i + number_human_players],
                   args.color_map,
                   args.target_map, 
                   game.state))

print(game.run(agents))
