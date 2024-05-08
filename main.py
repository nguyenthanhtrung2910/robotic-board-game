import pygame
import logging as log
import argparse

from Game.Board import Board
from Game.Game import Game
from Agents.DefaultAgent import DefaultAgent
from Agents.VirtualBoard import VirtualBoard

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
                    choices=['r', 'b', 'o', 'g', 'y'])
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
board = Board(args.color_map, args.target_map)
game = Game(board, args.required_mail, args.number_robots_with_same_color,
            args.robot_colors, render_mode='human', battery_considered=True)

for i in range(args.number_auto_players):
    agents.append(
        DefaultAgent(args.robot_colors[i + number_human_players],
                     VirtualBoard(args.color_map, args.target_map),
                     args.required_mail, game.state))

print(game.run(agents))
