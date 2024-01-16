import pygame
from src.consts import *
pygame.init()

class Cell:

    colors = {'w': (255,255,255), 'b':(0,0,255), 'r':(255,0,0), 'y':(255,255,0), 'gr':(0,255,0), 'g':(128, 128, 128)}
    mail_image = pygame.transform.scale(pygame.image.load('images/mail.png'), DEFAULT_IMAGE_SIZE)
    mail_number_images =[pygame.font.SysFont(None, 16).render(str(i), True, (255,0,0)) for i in range(1,10)]


    def __init__(self, y, x, color='w', target=0, robot=None, *,
                 front=None, back=None, left=None, right=None ) -> None:
        
        self.x = x
        self.y = y
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

    @property
    def adj(self):
        return [cell for cell in [self.front, self.back, self.left, self.right] if cell]

    def display(self, screen):
        pygame.draw.rect(screen, self.colors[self.color], ((self.x+1)*DEFAULT_IMAGE_SIZE[0], 
                                                            (self.y+1)*DEFAULT_IMAGE_SIZE[1], 
                                                            DEFAULT_IMAGE_SIZE[0], 
                                                            DEFAULT_IMAGE_SIZE[1]))  
        pygame.draw.rect(screen, (0,0,0), ((self.x+1)*DEFAULT_IMAGE_SIZE[0], 
                                            (self.y+1)*DEFAULT_IMAGE_SIZE[1], 
                                            DEFAULT_IMAGE_SIZE[0], 
                                            DEFAULT_IMAGE_SIZE[1]), 1) 
        if self.target:
            screen.blit(self.img, ((self.x+1)*DEFAULT_IMAGE_SIZE[0]+(DEFAULT_IMAGE_SIZE[0]-self.img.get_width())/2, 
                                   (self.y+1)*DEFAULT_IMAGE_SIZE[1]+(DEFAULT_IMAGE_SIZE[1]-self.img.get_height())/2))
        if self.robot:
            screen.blit(self.robot.img, ((self.x+1)*DEFAULT_IMAGE_SIZE[0], 
                                         (self.y+1)*DEFAULT_IMAGE_SIZE[1]))
            screen.blit(self.robot.number_img, ((self.x+1.5)*DEFAULT_IMAGE_SIZE[0] - self.robot.number_img.get_width()/2, 
                                                (self.y+1.7)*DEFAULT_IMAGE_SIZE[1] - self.robot.number_img.get_height()/2))
            if self.robot.mail:
                screen.blit(self.mail_image, ((self.x+1)*DEFAULT_IMAGE_SIZE[0], 
                                         (self.y+1)*DEFAULT_IMAGE_SIZE[1]))
                screen.blit(self.mail_number_images[self.robot.mail-1], ((self.x+1.5)*DEFAULT_IMAGE_SIZE[0], 
                                                                    (self.y+1.2)*DEFAULT_IMAGE_SIZE[1]))