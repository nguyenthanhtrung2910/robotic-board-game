import csv
import random
import pygame
import logging as log
import argparse
from src.Board import Board
from src.Cell import Cell
from src.Robot import Robot
from src.App import App
board = Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
robot = Robot(board[0][1], 1, 'r')
robot2 = Robot(board[1][0], 5, 'r')
print(all([True,True]))