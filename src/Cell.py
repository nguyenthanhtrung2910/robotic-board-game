import pygame
from src.consts import *
pygame.init()

class Cell:

    colors = {'w': (255,255,255), 'b':(0,0,255), 'r':(255,0,0), 'y':(255,255,0), 'gr':(0,255,0), 'g':(128, 128, 128)}

    def __init__(self, y, x, color='w', target=0, robot=None, *,
                 front=None, back=None, left=None, right=None ) -> None:
        
        self.__x = x
        self.__y = y
        self.color = color
        self.target = target
        self.robot = robot

        self.front = front
        self.back = back
        self.left = left
        self.right = right

        if self.target:
            target_font = pygame.font.SysFont(None, 64)
            self.img = target_font.render(str(self.target), True, (0,0,0))

    def __repr__(self) -> str:
        return f'Cell({self.x}, {self.y})'
    
    #equal and hash dunder method for using a Cell as dictionary's key
    def __eq__(self, cell):
        if isinstance(cell, Cell):
            return self.x == cell.x and self.y == cell.y 
        return NotImplemented

    def __hash__(self):
        return hash((self.x, self.y))    
    
    #less than dunder method for puttting a Cell in priority queue
    def __lt__(self, cell):
        if isinstance(cell, Cell):
            return True
        return NotImplemented

    @property
    def x(self):
        return self.__x
    
    @x.setter
    def x(self, x):
        raise ValueError('Don\'t change x')    
    
    @property
    def y(self):
        return self.__y
    
    @y.setter
    def y(self, y):
        raise ValueError('Don\'t change y')    

    @property
    def neighbors(self):
        return [cell for cell in [self.front, self.back, self.left, self.right] if cell]
    
    @property
    def priority(self):
        return sum([cell.robot != None for cell in self.neighbors])

    def display(self, surface):
        pygame.draw.rect(surface, self.colors[self.color], ((self.x+1)*DEFAULT_IMAGE_SIZE[0], 
                                                            (self.y+1)*DEFAULT_IMAGE_SIZE[1], 
                                                            DEFAULT_IMAGE_SIZE[0], 
                                                            DEFAULT_IMAGE_SIZE[1]))  
        pygame.draw.rect(surface, (0,0,0), ((self.x+1)*DEFAULT_IMAGE_SIZE[0], 
                                            (self.y+1)*DEFAULT_IMAGE_SIZE[1], 
                                            DEFAULT_IMAGE_SIZE[0], 
                                            DEFAULT_IMAGE_SIZE[1]), 1) 
        if self.target:
            surface.blit(self.img, ((self.x+1)*DEFAULT_IMAGE_SIZE[0]+(DEFAULT_IMAGE_SIZE[0]-self.img.get_width())/2, 
                                   (self.y+1)*DEFAULT_IMAGE_SIZE[1]+(DEFAULT_IMAGE_SIZE[1]-self.img.get_height())/2))