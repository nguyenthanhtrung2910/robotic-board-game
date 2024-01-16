import csv
import random
import pygame
import logging as log
import argparse
from src.Board import Board
from src.Cell import Cell
from src.Robot import Robot
from src.App import App
pygame.init()

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", help="chose colors map")
parser.add_argument("--target_map", help="chose targets map")
parser.add_argument("--required_mail", help="chose required mail to win", type=int)
parser.add_argument("--number_robot_per_player", help="chose number robot for each player. It shouldn't more than 5", default=3, type=int, choices=[1,2,3,4,5])
parser.add_argument("--player1_color", help="chose player 1 color", default='r', choices=['r','b','gr','y','w'])
parser.add_argument("--player2_color", help="chose player 2 color", default='b', choices=['r','b','gr','y','w'])
parser.add_argument("--player3_color", help="chose player 3 color",  choices=['r','b','gr','y','w'])
parser.add_argument("--player4_color", help="chose player 4 color",  choices=['r','b','gr','y','w'])
parser.add_argument("--player5_color", help="chose player 5 color",  choices=['r','b','gr','y','w'])
args = parser.parse_args()

log.basicConfig(level=log.INFO, 
                filename="events.log", 
                filemode="w", 
                format="%(levelname)s: At %(asctime)s %(message)s", 
                datefmt='%m/%d/%Y %I:%M:%S %p')

player_colors = [color for color in [args.player1_color, args.player2_color, args.player3_color, args.player4_color, args.player4_color, args.player5_color] if color]
app = App(args.color_map, args.target_map, args.required_mail, args.number_robot_per_player, player_colors)
app.run()
