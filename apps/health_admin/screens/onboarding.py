import pygame
from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
ORANGE = (255, 149, 0)
PURPLE = (175, 82, 222)
GREY = (142, 142, 147)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)


class AdminOnboardingScreen:

    def __init__(self):
        self.current_page = 0
        self.pages = [
            {
                "title": "Welcome to Admin",
                "description": "Manage your hospital efficiently with our comprehensive administration dashboard.",
                "icon": "admin"
            },
            {
                "title": "Manage Staff",
                "description": "Add, edit, and organize doctors and medical staff. Track their schedules and patients.",
                "icon": "staff"
            },
            {
                "title": "Track Everything",
                "description": "Monitor appointments, generate reports, and keep your hospital running smoothly.",
                "icon": "track"
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
            self.draw_button(screen, "Next", SCREEN_WIDTH // 2 - 150, 550, 300, 50, BLUE)
            self.draw_text_button(screen, "Skip", SCREEN_WIDTH // 2, 620, BLUE)
        else:
            self.draw_button(screen, "Get Started", SCREEN_WIDTH // 2 - 150, 550, 300, 50, BLUE)

    def draw_icon(self, screen, icon_type, x, y):
        if icon_type == "admin":
            pygame.draw.polygon(screen, BLUE, [
                (x, y - 50), (x + 50, y - 30), (x + 50, y + 20),
                (x, y + 50), (x - 50, y + 20), (x - 50, y - 30)
            ])
            pygame.draw.polygon(screen, (0, 100, 220), [
                (x, y - 40), (x + 40, y - 22), (x + 40, y + 15),
                (x, y + 40), (x - 40, y + 15), (x - 40, y - 22)
            ])
            pygame.draw.rect(screen, COLOR_WHITE, (x - 5, y - 25, 10, 50), border_radius=3)
            pygame.draw.rect(screen, COLOR_WHITE, (x - 20, y - 5, 40, 10), border_radius=3)

        elif icon_type == "staff":
            pygame.draw.circle(screen, GREEN, (x - 30, y - 15), 20)
            pygame.draw.circle(screen, GREEN, (x - 30, y - 35), 15)
            pygame.draw.circle(screen, BLUE, (x + 30, y - 15), 20)
            pygame.draw.circle(screen, BLUE, (x + 30, y - 35), 15)
            pygame.draw.circle(screen, PURPLE, (x, y + 10), 25)
            pygame.draw.circle(screen, PURPLE, (x, y - 20), 18)

        elif icon_type == "track":
            pygame.draw.rect(screen, ORANGE, (x - 50, y - 30, 100, 80), border_radius=10)
            pygame.draw.rect(screen, COLOR_WHITE, (x - 35, y + 10, 15, 30))
            pygame.draw.rect(screen, COLOR_WHITE, (x - 10, y - 10, 15, 50))
            pygame.draw.rect(screen, COLOR_WHITE, (x + 15, y + 0, 15, 40))
            pygame.draw.lines(screen, COLOR_WHITE, False, [
                (x - 40, y + 20), (x - 5, y - 5), (x + 20, y + 10), (x + 45, y - 20)
            ], 3)

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

    def draw_button(self, screen, text, x, y, width, height, color):
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, color, button_rect, border_radius=12)

        text_surface = FONT_BUTTON.render(text, True, COLOR_WHITE)
        text_x = x + (width - text_surface.get_width()) // 2
        text_y = y + (height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

    def draw_text_button(self, screen, text, center_x, y, color):
        text_surface = FONT_BODY.render(text, True, color)
        text_x = center_x - text_surface.get_width() // 2
        screen.blit(text_surface, (text_x, y))

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