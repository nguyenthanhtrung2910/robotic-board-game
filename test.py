import csv
import random
import pygame
import math, time, os
import logging as log
import argparse
from Game.Board import Board
from Game.Cell import Cell
from Game.Robot import Robot
from Game.Game import Game
from Agents.VirtualBoard import VirtualBoard
from Agents.VirtualCell import VirtualCell
from Agents.VirtualRobot import VirtualRobot
from Agents.VirtualGame import VirtualGame
from Agents.DefaultAgent import DefaultAgent
pygame.init()

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", help="chose colors map")
parser.add_argument("--target_map", help="chose targets map")
parser.add_argument("--required_mail", help="chose required mail to win", type=int)
parser.add_argument("--number_robots_with_same_color", 
                    help="chose number robots with same color. It shouldn't more than 6",
                    default=3,
                    type=int,
                    choices=[1,2,3,4,5,6,7,8])
parser.add_argument("--robot_colors", help="chose robot colors", nargs="+", choices=['r','b','o','g','y'])
parser.add_argument("--number_auto_players", help="chose number auto-players", type = int)

args = parser.parse_args()
log.basicConfig(level=log.INFO)
root_logger = log.getLogger()

board = Board(args.color_map, args.target_map)
number_human_players = len(args.robot_colors) - args.number_auto_players
agents = []
game = Game(board, args.required_mail, args.number_robots_with_same_color, args.robot_colors)
for i in range(args.number_auto_players):
    agents.append(DefaultAgent(args.robot_colors[i+number_human_players],
                               VirtualBoard(args.color_map, args.target_map),
                               args.required_mail,
                               game.state))

i=0
while i <= 99:
    print('sample {}'.format(i))
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    filename = 'log_files_for_{}x{}/events(sample {}).log'.format(len(args.robot_colors), args.number_robots_with_same_color, i)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    new_file_handler = log.FileHandler(filename, mode='w')
    new_file_handler.setLevel(log.INFO)
    new_file_handler.setFormatter(log.Formatter("%(levelname)s: %(message)s"))
    root_logger.addHandler(new_file_handler)

    winner, t = game.run(agents)
    print(f'winner: {winner}, time: {t}')

    game.reset(args.number_robots_with_same_color, args.robot_colors)
    for agent in agents:
        agent.reset(game.state)

    if winner != None:
        i += 1 
