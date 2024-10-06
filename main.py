import pygame
import logging as log
import argparse

from src.game.robotic_board_game import Game
from src.a_star_agent import AStarAgent

pygame.init()

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", help="chose colors map")
parser.add_argument("--target_map", help="chose targets map")
parser.add_argument("--required_mail",
                    help="chose required mail to win",
                    type=int)
parser.add_argument(
    "--number_robots_per_player",
    help="chose number robots per player. It shouldn't more than 6",
    default=3,
    type=int,
    choices=[1, 2, 3, 4, 5, 6])
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
agents = []
game = Game(args.color_map, 
            args.target_map, 
            args.required_mail, 
            args.number_robots_per_player,
            args.robot_colors, 
            render_mode='human', 
            max_step=500,
            battery_considered=True)
a_star = AStarAgent(args.color_map,
                    args.target_map, 
                    game.number_robots,
                    game.robots[game.agent_selection].battery)
for _ in range(args.number_auto_players):
    for _ in range(args.number_robots_per_player):
        agents.append(a_star)

print(game.run(agents))
