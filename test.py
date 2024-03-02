import random
import pygame
import logging as log

import src
from src.Cell import Cell
from src.Board import Board
from src.Robot import Robot
from src.Mail import Mail
from src.Clock import Clock
from src.Player import Player
from src.Computer import Computer
from src.consts import *

pygame.init()
screen = pygame.display.set_mode((DEFAULT_IMAGE_SIZE[0]*28, DEFAULT_IMAGE_SIZE[1]*11)) 
pygame.display.set_caption('Robotics Board Game')
# clock = pygame.time.Clock() 
nomove_count = 0
winner = None
running = True
while running:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            running = False
    screen.fill((0, 0, 255))
    pygame.display.flip()

running = True
while running:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            running = False           
    screen.fill((0, 255, 0))
    pygame.display.flip()