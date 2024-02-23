import csv
import random
import pygame
import logging as log
import argparse
from statistics import mean
from src.Board import Board
from src.Cell import Cell
from src.Robot import Robot
from src.App import App
pygame.init()

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", help="chose colors map")
parser.add_argument("--target_map", help="chose targets map")
args = parser.parse_args()

board = Board(args.color_map, args.target_map)
file = open('game_time_by_number_player.txt', 'a')
colors = ['r', 'w', 'b', 'gr', 'y', 'o']

for k in range(2,7,1):
    i = 0
    result = []
    while i <= 100:
        app = App(board, 50, 2, ['computer']*k, colors[:k])
        winner, time = app.run()
        board.reset()
        if winner:
            result.append(time)
            i += 1
        # print(i)
    file.write('{}: {}\n'.format(k, mean(result)))   
    print('for {} player done !'.format(k))

file.close()
