import csv
import random
import pygame
import logging as log
import argparse
from statistics import mean
from src.Board import Board
from src.Cell import Cell
from src.Robot import Robot
from src.Game import App
pygame.init()

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", help="chose colors map")
parser.add_argument("--target_map", help="chose targets map")
parser.add_argument("--required_mail", help="chose required mail to win", type=int)
parser.add_argument("--number_robot_per_player", help="chose number robot for each player. It shouldn't more than 5", default=3, type=int, choices=[1,2,3,4,5,6,7,8,9,10])
parser.add_argument("--player1_color", help="chose player 1 color", default='r', choices=['r','b','gr','y','w','o'])
parser.add_argument("--player1_type", help="chose player 1 type", default='computer', choices=['player', 'computer'])

parser.add_argument("--player2_color", help="chose player 2 color", default='b', choices=['r','b','gr','y','w','o'])
parser.add_argument("--player2_type", help="chose player 2 type", default='computer', choices=['player', 'computer'])

parser.add_argument("--player3_color", help="chose player 3 color",  choices=['r','b','gr','y','w','o'])
parser.add_argument("--player3_type", help="chose player 3 type", choices=['player', 'computer'])
parser.add_argument("--player4_color", help="chose player 4 color",  choices=['r','b','gr','y','w','o'])
parser.add_argument("--player4_type", help="chose player 4 type", choices=['player', 'computer'])
parser.add_argument("--player5_color", help="chose player 5 color",  choices=['r','b','gr','y','w','o'])
parser.add_argument("--player5_type", help="chose player 5 type", choices=['player', 'computer'])
parser.add_argument("--player6_color", help="chose player 6 color",  choices=['r','b','gr','y','w','o'])
parser.add_argument("--player6_type", help="chose player 6 type", choices=['player', 'computer'])
args = parser.parse_args()

log.basicConfig(level=log.INFO, 
                filename="events.log", 
                filemode="w", 
                format="%(levelname)s: %(message)s")

player_colors = [color for color in [args.player1_color, args.player2_color, args.player3_color, args.player4_color, args.player4_color, args.player5_color] if color]
player_types = [type for type in [args.player1_type, args.player2_type, args.player3_type, args.player4_type, args.player4_type, args.player5_type] if type]
board = Board(args.color_map, args.target_map)
app = App(board, args.required_mail, args.number_robot_per_player, player_types, player_colors)
print(app.run())
