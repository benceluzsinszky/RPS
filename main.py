import pygame
import pygame_widgets
import sys
import random

from pygame_widgets.slider import Slider
from scipy.spatial import KDTree

from sprites import Sprite

RESX = RESY = 500
BG_COLOR = (255, 249, 222)


class Game():

    def __init__(self) -> None:
        """
        Initializes Pygame module and creates game screen.
        """
        pygame.init()

        self.clock = pygame.time.Clock()

        pygame.display.set_caption("Rock Paper Scissors")
        icon = pygame.image.load('sprites/logo.png')
        pygame.display.set_icon(icon)

        flags = pygame.HWSURFACE | pygame.DOUBLEBUF  # enable hardware acceleration
        self.screen = pygame.display.set_mode((RESX, RESY), flags)
        self.font = pygame.font.Font("font/PressStart2P-vaV7.ttf", 24)

        self.group_size = 50
        self.click = False

    def main_menu(self):
        """Run the main loop for the menu."""

        self.speed_slider = Slider(
            self.screen,
            100, 150, 300, 15,
            min=1, max=10, step=1, initial=2,
            colour=(166, 208, 221),
            handleColour=(87, 117, 127))

        self.group_slider = Slider(
            self.screen,
            100, 250, 300, 15,
            min=1, max=150, step=1, initial=50,
            colour=(166, 208, 221),
            handleColour=(87, 117, 127))

        while True:
            self.screen.fill(BG_COLOR)

            self.click = False
            self.check_events()

            slider_font = pygame.font.Font("font/PressStart2P-vaV7.ttf", 14)

            self.speed = self.speed_slider.getValue()
            speed_image = slider_font.render(f"Speed: {self.speed}", 1, (43, 57, 61))
            speed_rect = speed_image.get_rect()
            speed_rect.center = (250, 175)
            self.screen.blit(speed_image, speed_rect)

            self.group_size = self.group_slider.getValue()
            counter_image = slider_font.render(f"Group size: {self.group_size}", 1, (43, 57, 61))
            counter_rect = counter_image.get_rect()
            counter_rect.center = (250, 275)
            self.screen.blit(counter_image, counter_rect)

            play_image = self.font.render("PLAY", 1, (43, 57, 61))
            play_rect = play_image.get_rect()
            play_rect.center = (250, 350)

            # get mouse position
            mx, my = pygame.mouse.get_pos()
            # make play text colored when mouse is hovered on it
            if play_rect.collidepoint(mx, my):
                play_image = self.font.render("PLAY", 1, (75, 100, 110))
                if self.click:
                    self.speed_slider.hide()
                    self.group_slider.hide()
                    self.run_game()

            self.screen.blit(play_image, play_rect)

            pygame_widgets.update(pygame.event.get())
            pygame.display.flip()
            self.clock.tick(60)

    def run_game(self):
        """
        Starts the game loop that continues until the user exits the game.
        """
        self.click = False

        self.rocks = pygame.sprite.Group()
        self.papers = pygame.sprite.Group()
        self.scissors = pygame.sprite.Group()

        self.sprite_groups = [self.rocks, self.papers, self.scissors]

        self.create_sprites("rock", self.rocks)
        self.create_sprites("paper", self.papers)
        self.create_sprites("scissors", self.scissors)

        self.get_sprite_locations()

        while True:
            self.check_events()
            self.move_sprites(
                self.rock_tree, self.rock_list,
                self.scissors_tree, self.scissors_list,
                self.paper_tree, self.paper_list
                )
            self.move_sprites(
                self.paper_tree, self.paper_list,
                self.rock_tree, self.rock_list,
                self.scissors_tree, self.scissors_list
                )
            self.move_sprites(
                self.scissors_tree, self.scissors_list,
                self.paper_tree, self.paper_list,
                self.rock_tree, self.rock_list
                )
            self.get_sprite_locations()
            self.check_collisions()
            self.update_screen()
            self.clock.tick(60)

    def game_over(self):
        """
        Game over screen, that shows the winner.
        """
        while self.game_over:
            self.screen.fill(BG_COLOR)

            if self.winner_group == self.rocks:
                winner = "ROCK"
            elif self.winner_group == self.papers:
                winner = "PAPER"
            elif self.winner_group == self.scissors:
                winner = "SCISSORS"

            winner_image = self.font.render(f"{winner} WON!", 1, (43, 57, 61))
            winner_rect = winner_image.get_rect()
            winner_rect.center = (250, 200)

            restart_image = self.font.render("Restart", 1, (43, 57, 61))
            restart_rect = restart_image.get_rect()
            restart_rect.center = (250, 300)

            mx, my = pygame.mouse.get_pos()
            if restart_rect.collidepoint(mx, my):
                restart_image = self.font.render("Restart", 1, (75, 100, 110))
                if self.click:
                    self.run_game()

            menu_image = self.font.render("Main menu", 1, (43, 57, 61))
            menu_rect = menu_image.get_rect()
            menu_rect.center = (250, 350)

            mx, my = pygame.mouse.get_pos()
            if menu_rect.collidepoint(mx, my):
                menu_image = self.font.render("Main menu", 1, (75, 100, 110))
                if self.click:
                    self.main_menu()

            self.screen.blit(winner_image, winner_rect)
            self.screen.blit(restart_image, restart_rect)
            self.screen.blit(menu_image, menu_rect)

            self.check_events()
            pygame.display.flip()
            self.clock.tick(60)

    def update_screen(self):
        """
        Updates the game screen with new information.
        """
        self.screen.fill(BG_COLOR)
        self.draw_score()

        for group in self.sprite_groups:
            if len(group) == self.group_size * 3:
                self.winner_group = group
                self.game_over()
            for sprite in group:
                sprite.blit_sprite()

        pygame.display.flip()

    def check_events(self):
        """
        Checks for user input events such as key presses or window close events.
        """
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.click = True

    def get_sprite_locations(self):
        """
        Creates a kd-tree to search for nearby sprites.
        """
        rock_locations = [(sprite.rect.centerx, sprite.rect.centery) for sprite in self.rocks]
        try:
            self.rock_tree = KDTree(rock_locations)
        except ValueError:
            ...
        self.rock_list = [sprite for sprite in self.rocks]
        paper_locations = [(sprite.rect.centerx, sprite.rect.centery) for sprite in self.papers]
        try:
            self.paper_tree = KDTree(paper_locations)
        except ValueError:
            ...
        self.paper_list = [sprite for sprite in self.papers]
        scissors_locations = [(sprite.rect.centerx, sprite.rect.centery) for sprite in self.scissors]
        try:
            self.scissors_tree = KDTree(scissors_locations)
        except ValueError:
            ...
        self.scissors_list = [sprite for sprite in self.scissors]

    def collision(self, hunter_group, food_group, type):
        """
        Kills food sprite, creates a new sprite in the 'hunter' group
        """
        for hunter in hunter_group:
            for food in food_group:
                collision = pygame.sprite.collide_rect(
                    hunter, food)

                if collision:
                    sprite = Sprite(
                        self, type, (food.rect.x, food.rect.y))
                    hunter_group.add(sprite)
                    food.kill()

    def check_collisions(self):
        """
        Check for collisions between sprite groups.
        """
        self.collision(self.rocks, self.scissors, "rock")
        self.collision(self.scissors, self.papers, "scissors")
        self.collision(self.papers, self.rocks, "paper")

    def move_sprites(self, current_tree, current_list, food_tree, food_list, enemy_tree, enemy_list):
        """
        Makes sprites move.
        """
        for sprite in current_list:
            sprite.action(current_tree, current_list, food_tree, food_list, enemy_tree, enemy_list)

    def create_sprites(self, type, group):
        """
        Generates initial sprites.
        """
        for _ in range(self.group_size):
            random_x = random.randint(10, 490)
            random_y = random.randint(10, 490)
            sprite = Sprite(self, type, (random_x, random_y))
            group.add(sprite)

    def draw_score(self):
        """
        Draw score lines on the bottom.
        """
        multipilier = RESX / (self.group_size * 3)

        len_rocks = (len(self.rocks) * multipilier)
        len_papers = (len(self.papers) * multipilier)

        pygame.draw.rect(self.screen, (166, 208, 221), [0, RESY-25, len_rocks, RESY])
        pygame.draw.rect(self.screen, (255, 211, 176), [
                         len_rocks, RESY-25, len_papers, RESY])
        pygame.draw.rect(self.screen, (255, 105, 105), [
                         len_rocks+len_papers-2, RESY-25, RESX, RESY])


if __name__ == "__main__":
    game = Game()
    game.main_menu()
