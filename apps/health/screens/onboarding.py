import pygame

from apps.health.components import draw_button, draw_text_button
from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
PINK = (255, 45, 85)
GREY = (142, 142, 147)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)


class OnboardingScreen:

    def __init__(self):
        self.current_page = 0
        self.pages = [
            {
                "title": "Welcome to Health",
                "description": "Your personal health companion that helps you track your daily activities and wellness goals.",
                "icon": "heart"
            },
            {
                "title": "Track Your Activity",
                "description": "Monitor your steps, calories burned, and exercise minutes throughout the day.",
                "icon": "activity"
            },
            {
                "title": "Monitor Your Health",
                "description": "Keep track of your heart rate, sleep patterns, and other vital health metrics.",
                "icon": "monitor"
            }
        ]

        self.swipe_start_x = None
        self.swipe_start_time = None
        self.swipe_threshold = 50
        self.ignore_next_mouseup = False

    def reset_swipe(self):
        self.swipe_start_x = None
        self.swipe_start_time = None
        self.ignore_next_mouseup = True

    def draw(self, screen):
        screen.fill(COLOR_WHITE)

        page = self.pages[self.current_page]

        self.draw_icon(screen, page["icon"], SCREEN_WIDTH // 2, 180)

        title = FONT_TITLE.render(page["title"], True, COLOR_BLACK)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(title, (title_x, 320))

        self.draw_wrapped_text(screen, page["description"], 40, 370, SCREEN_WIDTH - 80)

        self.draw_page_dots(screen, 480)

        if self.current_page < len(self.pages) - 1:
            draw_button(screen, "Next", SCREEN_WIDTH // 2 - 150, 550, 300, 50, BLUE)
            draw_text_button(screen, "Skip", SCREEN_WIDTH // 2, 620, BLUE)
        else:
            draw_button(screen, "Get Started", SCREEN_WIDTH // 2 - 150, 550, 300, 50, BLUE)

    def draw_icon(self, screen, icon_type, x, y):
        if icon_type == "heart":
            pygame.draw.circle(screen, RED, (x - 25, y), 35)
            pygame.draw.circle(screen, RED, (x + 25, y), 35)
            points = [(x - 60, y + 10), (x, y + 70), (x + 60, y + 10)]
            pygame.draw.polygon(screen, RED, points)
        elif icon_type == "activity":
            pygame.draw.circle(screen, RED, (x, y), 50, 10)
            pygame.draw.circle(screen, GREEN, (x, y), 35, 8)
            pygame.draw.circle(screen, BLUE, (x, y), 22, 6)
        elif icon_type == "monitor":
            pygame.draw.rect(screen, PINK, (x - 50, y - 30, 100, 60), border_radius=15)
            points = [
                (x - 40, y), (x - 20, y), (x - 10, y - 20),
                (x, y + 15), (x + 10, y - 25), (x + 20, y), (x + 40, y)
            ]
            pygame.draw.lines(screen, COLOR_WHITE, False, points, 3)

    def draw_page_dots(self, screen, y):
        total = len(self.pages)
        dot_spacing = 12
        start_x = (SCREEN_WIDTH - (total * dot_spacing)) // 2

        for i in range(total):
            dot_x = start_x + i * dot_spacing
            color = BLUE if i == self.current_page else (200, 200, 200)
            pygame.draw.circle(screen, color, (dot_x, y), 4)

    def draw_wrapped_text(self, screen, text, x, y, max_width):
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = FONT_BODY.render(test_line, True, GREY)
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        for line in lines:
            text_surface = FONT_BODY.render(line, True, GREY)
            text_x = (SCREEN_WIDTH - text_surface.get_width()) // 2
            screen.blit(text_surface, (text_x, y))
            y += FONT_BODY.get_height() + 4

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.ignore_next_mouseup = False
            self.swipe_start_x = event.pos[0]
            self.swipe_start_time = pygame.time.get_ticks()

            x, y = event.pos

            if 550 < y < 600 and SCREEN_WIDTH // 2 - 150 < x < SCREEN_WIDTH // 2 + 150:
                if self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                    return None
                else:
                    self.reset_swipe()
                    return "login"

            if 610 < y < 640 and self.current_page < len(self.pages) - 1:
                self.reset_swipe()
                return "login"

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.ignore_next_mouseup:
                self.ignore_next_mouseup = False
                self.swipe_start_x = None
                return None

            if self.swipe_start_x is not None:
                swipe_distance = event.pos[0] - self.swipe_start_x
                swipe_time = pygame.time.get_ticks() - (self.swipe_start_time or 0)

                if swipe_time < 500:
                    if swipe_distance < -self.swipe_threshold:
                        if self.current_page < len(self.pages) - 1:
                            self.current_page += 1
                        else:
                            self.swipe_start_x = None
                            return "login"

                    elif swipe_distance > self.swipe_threshold:
                        if self.current_page > 0:
                            self.current_page -= 1

                self.swipe_start_x = None
                self.swipe_start_time = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            elif event.key == pygame.K_RIGHT:
                if self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                else:
                    return "login"
            elif event.key == pygame.K_LEFT:
                if self.current_page > 0:
                    self.current_page -= 1

        return None