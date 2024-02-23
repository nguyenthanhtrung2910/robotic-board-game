import random
import pygame
import src
from src.Cell import Cell
from src.Board import Board
from src.Robot import Robot
from src.Player import Player
from src.Computer import Computer
from src.Mail import Mail
from src.Clock import Clock
from src.consts import *
pygame.init()
class App:

    # font1 = pygame.font.SysFont(None, 64)
    images_for_cell_coordinate =[pygame.font.SysFont(None, 48).render(str(i), True,(0,0,0)) for i in range(9)]

    def __init__(self, board, required_mail, number_robot_per_player, player_types, player_colors) -> None:

        self.screen = pygame.display.set_mode((DEFAULT_IMAGE_SIZE[0]*28, DEFAULT_IMAGE_SIZE[1]*11)) 
        pygame.display.set_caption('Robotics Board Game') 
        self.game_clock = Clock()
        self.sprites = pygame.sprite.Group()
        self.running = True

        self.board = board
        self.required_mail = required_mail
        self.number_robot_per_player = number_robot_per_player
        self.number_players = len(player_colors)

        robot_cells_init = random.sample(self.board.white_cells, k = self.number_robot_per_player*len(player_colors))
        self.players = []
        for i, (player_type, player_color) in enumerate(zip(player_types,player_colors)):
            self.players.append(getattr(src, player_type.capitalize())(robot_cells_init[self.number_robot_per_player*i:self.number_robot_per_player*i+self.number_robot_per_player], 
                                                                       player_color, self.sprites, self.game_clock, self.board))

        #draw a background
        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill((255, 255, 255))
        #draw board
        for i in range(self.board.size):
            for j in range(self.board.size):
                self.board[i][j].display(self.background)

        for i in range(self.board.size):     
            self.background.blit(self.images_for_cell_coordinate[i], ((i+1)*DEFAULT_IMAGE_SIZE[0]+(DEFAULT_IMAGE_SIZE[0]-self.images_for_cell_coordinate[i].get_width())/2, 
                                                                    (DEFAULT_IMAGE_SIZE[1]-self.images_for_cell_coordinate[i].get_height())/2))
            self.background.blit(self.images_for_cell_coordinate[i], ((DEFAULT_IMAGE_SIZE[0]-self.images_for_cell_coordinate[i].get_width())/2, 
                                                                    (i+1)*DEFAULT_IMAGE_SIZE[1]+(DEFAULT_IMAGE_SIZE[1]-self.images_for_cell_coordinate[i].get_height())/2))
        #draw baterry bar
        for j in range(self.number_players*self.number_robot_per_player):
            for i in range(MAXIMUM_ROBOT_BATTERY+1):
                rect = pygame.Rect(10.5*DEFAULT_IMAGE_SIZE[0]+i*CELL_BATTERY_SIZE[0], 
                                  (DEFAULT_IMAGE_SIZE[1]*11 - CELL_BATTERY_SIZE[1]*self.number_robot_per_player*self.number_players)/2 +j*CELL_BATTERY_SIZE[1], 
                                   CELL_BATTERY_SIZE[0], 
                                   CELL_BATTERY_SIZE[1])    
                pygame.draw.rect(self.background, (0,0,0), rect, 1) 
        
        self.sprites.add([robot for player in self.players for robot in player.robots])
        
    def run(self):
        nomove_count = 0
        winner = None
        # clock = pygame.time.Clock()
        chosen_player = self.players[0]
        game_over = False
        while self.running:
            self.screen.blit(self.background, (0,0))
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: 
                    self.running = False
                #player finish turn
                if event.type == pygame.KEYDOWN and not game_over:
                    if event.key == pygame.K_f:
                        chosen_player = self.players[(self.players.index(chosen_player)+1)%self.number_players]
                        for robot in chosen_player.robots:
                            robot.allowed_step_per_turn = 1

            #chosen player movement
            if not game_over: 
                if not chosen_player.move(self.board):
                    nomove_count += 1 
                else:
                    nomove_count = 0

            #computer finish turn
            if not game_over and type(chosen_player) != Player:
                # if chosen_player.frame_count == self.number_robot_per_player*FRAME_PER_MOVE:
                    chosen_player = self.players[(self.players.index(chosen_player)+1)%self.number_players]
                    for robot in chosen_player.robots:
                        robot.allowed_step_per_turn = 1
            
            #game over checking 
            if chosen_player.count_mail == self.required_mail:
                game_over = True
                winner = self.players.index(chosen_player)
                return winner, self.game_clock.now

                # img = self.font1.render(f"Player {Robot.colors_map[chosen_player.color]} win", True, Cell.colors[chosen_player.color])
                # self.screen.blit(img, (9*DEFAULT_IMAGE_SIZE[0]+(18*DEFAULT_IMAGE_SIZE[0]-img.get_width())/2, 0))

            #when all player skip their turn so DRAW
            if nomove_count == self.number_players:
                game_over = True
                return winner, self.game_clock.now

                # img = self.font1.render("Draw", True, Cell.colors[chosen_player.color])
                # self.screen.blit(img, (9*DEFAULT_IMAGE_SIZE[0]+(18*DEFAULT_IMAGE_SIZE[0]-img.get_width())/2, 0))
            
            #draw all sprites
            self.sprites.draw(self.screen)

            for i, player in enumerate(self.players):
                for robot in player.robots:
                    pygame.draw.circle(self.screen, Cell.colors[robot.color], 
                                       (10.5*DEFAULT_IMAGE_SIZE[0]+(robot.battery)*CELL_BATTERY_SIZE[0]+CELL_BATTERY_SIZE[0]/2,
                                       (DEFAULT_IMAGE_SIZE[1]*11 - CELL_BATTERY_SIZE[1]*self.number_robot_per_player*self.number_players)/2+(i*self.number_robot_per_player+robot.index-1)*CELL_BATTERY_SIZE[1]+CELL_BATTERY_SIZE[1]/2), 
                                       CELL_BATTERY_SIZE[0]/2*0.8, 0)
            
            # pygame.draw.rect(self.screen, (255,0,0), ((chosen_player.chosen_robot.pos.x+1)*DEFAULT_IMAGE_SIZE[0], 
            #                                         (chosen_player.chosen_robot.pos.y+1)*DEFAULT_IMAGE_SIZE[1], 
            #                                         DEFAULT_IMAGE_SIZE[0], 
            #                                         DEFAULT_IMAGE_SIZE[1]), 2) 
            pygame.display.update()
            # clock.tick(FRAME_PER_SECOND)
        return winner, self.game_clock.now