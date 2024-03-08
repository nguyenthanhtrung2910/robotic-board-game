import pygame
from Game.consts import *
pygame.init()

class Cell:

    colors = {'w': (255,255,255), 'b':(0,0,255), 'r':(255,0,0), 'y':(255,255,0), 'gr':(0,255,0), 'g':(128, 128, 128), 'o':(255,165,0)}

    def __init__(self, y, x, color='w', target=0, robot=None, *,
                 front=None, back=None, left=None, right=None ) -> None:
        
        self.__x = x
        self.__y = y
        self.__color = color
        self.__target = target
        self.robot = robot

        self.front = front
        self.back = back
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f'Cell({self.x}, {self.y})'
    
    #equal and hash dunder method for using a Cell as dictionary's key
    def __eq__(self, cell):
        if isinstance(cell, Cell):
            return self.x == cell.x and self.y == cell.y 
        return NotImplemented

    def __hash__(self):
        return hash((self.x, self.y))    
    @property
    def x(self):
        return self.__x
    
    @x.setter
    def x(self, x):
        raise ValueError('You can\'t change cell coordinate')    
    
    @property
    def y(self):
        return self.__y
    
    @y.setter
    def y(self, y):
        raise ValueError('You can\'t change cell coordinate')    
    
    @property
    def color(self):
        return self.__color
    
    @color.setter
    def color(self, color):
        raise ValueError('You can\'t change cell color')    
    
    @property
    def target(self):
        return self.__target
    
    @target.setter
    def target(self, target):
        raise ValueError('You can\'t change cell target') 

    @property
    def neighbors(self):
        return [cell for cell in [self.front, self.back, self.left, self.right] if cell]

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.colors[self.color], ((self.x+1)*CELL_SIZE[0], 
                                                            (self.y+1)*CELL_SIZE[1], 
                                                            CELL_SIZE[0], 
                                                            CELL_SIZE[1]))  
        pygame.draw.rect(surface, (0,0,0), ((self.x+1)*CELL_SIZE[0], 
                                            (self.y+1)*CELL_SIZE[1], 
                                            CELL_SIZE[0], 
                                            CELL_SIZE[1]), 1) 
        if self.target:
            target_font = pygame.font.SysFont(None, 64)
            target_image = target_font.render(str(self.target), True, (0,0,0))
            surface.blit(target_image, 
                        ((self.x+1)*CELL_SIZE[0]+(CELL_SIZE[0]-target_image.get_width())/2, 
                        (self.y+1)*CELL_SIZE[1]+(CELL_SIZE[1]-target_image.get_height())/2))