import pygame
import math

from pygame.sprite import Sprite


class Sprite(Sprite):
    """
    Class that creats a Rock/Papaer/Scissor character.
    """
    def __init__(self, game, character=str, location=tuple) -> None:
        super().__init__()
        self.screen = game.screen
        self.image = pygame.image.load(f"sprites/{character}.png")
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.image.set_colorkey((255, 255, 255))
        self.rect = location
        self.closest_food = None
        self.closest_food_distance = float("inf")

    def blit_sprite(self):
        self.screen.blit(self.image, self.rect)

    def get_food_info(self, food):
        for sprite in food:
            distance = math.sqrt((
                sprite.rect[0] - self.rect[1])**2 + (sprite.rect[1] - self.rect.centery)**2)
            if distance < self.closest_food_distance:
                self.closest_food_distance = distance
                self.closest_food = sprite

    def eat(self):
        direction = pygame.math.Vector2(self.closest_food.rect.center) - pygame.math.Vector2(self.rect.center)
        direction.normalize_ip()
        self.rect.move_ip(direction * 5)
