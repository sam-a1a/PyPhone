import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CORNER_RADIUS, COLOR_WHITE, COLOR_BLACK
from components import draw_status_bar

class BaseApp:

    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.app_name = "App"
        self.background_color = COLOR_WHITE
        self.dark_status_bar = False  # Light background = dark text

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if x < 70 and 40 < y < 90:
                self.close()

    def update(self):
        pass

    def draw(self):
        self.screen.fill(self.background_color)
        self.draw_header()
        draw_status_bar(self.screen, dark_mode=self.dark_status_bar)
        self.draw_bezel()

    def draw_bezel(self):
        pygame.draw.rect(
            self.screen, COLOR_BLACK,
            (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            10, border_radius=CORNER_RADIUS
        )

    def draw_header(self):
        font = pygame.font.SysFont("Arial", 18)
        back_text = font.render("< Back", True, (0, 122, 255))
        self.screen.blit(back_text, (15, 50))

        title_font = pygame.font.SysFont("Arial", 20, bold=True)
        title = title_font.render(self.app_name, True, COLOR_BLACK)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        self.screen.blit(title, (title_x, 50))

    def close(self):
        self.running = False

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return "quit"
                self.handle_event(event)

            self.update()
            self.draw()

            pygame.display.flip()
            clock.tick(60)

        return "home"