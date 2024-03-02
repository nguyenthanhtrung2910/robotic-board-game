import csv
import random
import pygame
import math
import logging as log
import argparse
from statistics import mean, stdev
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
log.basicConfig(level=log.INFO)
root_logger = log.getLogger()
for j in range(2,4,1):
    for k in range(2,5,1):
        i = 0
        result = []
        while i <= 99:
            print('sample {}'.format(i))

            for handler in root_logger.handlers:
                root_logger.removeHandler(handler)
            new_file_handler = log.FileHandler('log_files/events for {} robots per player and {} players (sample {}).log'.format(j, k, i), mode='w')
            new_file_handler.setLevel(log.INFO)
            new_file_handler.setFormatter(log.Formatter("%(levelname)s: %(message)s"))
            root_logger.addHandler(new_file_handler)

            app = App(board, 50, j, ['computer']*k, colors[:k])
            winner, time = app.run()
            print(f'winner: {winner}, time: {time}')
            board.reset()
            if winner != None:
                result.append(time)
                i += 1 
        file.write('{} robot for each player and {} players: t={:.2f}\u00B1{:05.2f} \n'.format(j, k, mean(result), math.sqrt(1/len(result))*stdev(result)))   
        print('for {} player done !'.format(k))

file.close()
