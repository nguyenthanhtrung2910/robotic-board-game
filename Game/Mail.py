import pygame
from Game.consts import *
class Mail(pygame.sprite.Sprite):
    def __init__(self, mail_number, robot=None):
        super().__init__()
        self.mail_number = mail_number
        self.robot = robot
        self.image = pygame.transform.scale(pygame.image.load('images/mail.png'), CELL_SIZE)
        mail_number_images = pygame.font.SysFont(None, 16).render(str(self.mail_number), True, (255,0,0))
        self.image.blit(mail_number_images, (0.5*CELL_SIZE[0], 0.2*CELL_SIZE[1]))

    @property
    def rect(self):
        rect = self.image.get_rect()
        rect.topleft = ((self.robot.pos.x+1)*CELL_SIZE[0], (self.robot.pos.y+1)*CELL_SIZE[1])
        return rect
