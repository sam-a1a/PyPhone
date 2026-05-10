import pygame
import os
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK

BLUE = (66, 133, 244)
RED = (234, 67, 53)
YELLOW = (251, 188, 5)
GREEN = (52, 168, 83)
GREY = (142, 142, 147)
LIGHT_GREY = (245, 245, 247)
PURPLE = (156, 39, 176)

FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_LARGE = pygame.font.SysFont("Arial", 24, bold=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")


class GoogleSignInModal:

    def __init__(self):
        self.state = "initial"
        self.animation_progress = 0
        self.slide_progress = 0
        self.success_progress = 0
        self.modal_height = 500
        self.selected_account = None

        self.accounts = [
            {"name": "Bassam", "email": "bassam@gmail.com", "avatar_color": BLUE},
            {"name": "Jihan", "email": "jihan@gmail.com", "avatar_color": PURPLE},
        ]

        self.google_logo = None
        self.load_google_logo()

        self.slide_speed = 30

    def load_google_logo(self):
        logo_path = os.path.join(ICON_DIR, "google.png")
        if os.path.exists(logo_path):
            try:
                self.google_logo = pygame.image.load(logo_path).convert_alpha()
                self.google_logo = pygame.transform.smoothscale(self.google_logo, (40, 40))
            except (pygame.error, OSError):
                pass

    def reset(self):
        self.state = "initial"
        self.animation_progress = 0
        self.slide_progress = 0
        self.success_progress = 0
        self.selected_account = None

    def update(self):
        if self.slide_progress < self.modal_height:
            self.slide_progress = min(self.slide_progress + self.slide_speed, self.modal_height)

        if self.state == "loading":
            self.animation_progress += 5
            if self.animation_progress >= 100:
                self.state = "success"
                self.success_progress = 0

        if self.state == "success":
            self.success_progress += 8
            if self.success_progress >= 150:
                return "complete"

        return None

    def draw(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_alpha = min(150, int(self.slide_progress / self.modal_height * 150))
        overlay.fill((0, 0, 0, overlay_alpha))
        screen.blit(overlay, (0, 0))

        modal_y = SCREEN_HEIGHT - self.slide_progress

        modal_surface = pygame.Surface((SCREEN_WIDTH, self.modal_height), pygame.SRCALPHA)
        pygame.draw.rect(modal_surface, COLOR_WHITE, (0, 0, SCREEN_WIDTH, self.modal_height),
                        border_top_left_radius=20, border_top_right_radius=20)
        screen.blit(modal_surface, (0, modal_y))

        bar_width = 40
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, modal_y + 10, bar_width, 5), border_radius=3)

        if self.state == "initial":
            self.draw_initial_state(screen, modal_y)
        elif self.state == "accounts":
            self.draw_accounts_state(screen, modal_y)
        elif self.state == "loading":
            self.draw_loading_state(screen, modal_y)
        elif self.state == "success":
            self.draw_success_state(screen, modal_y)

    def draw_google_logo_fallback(self, screen, x, y, size=40):
        center = (x + size // 2, y + size // 2)
        radius = size // 2 - 2

        pygame.draw.circle(screen, RED, center, radius)
        pygame.draw.circle(screen, COLOR_WHITE, center, radius - 8)

        pygame.draw.rect(screen, BLUE, (center[0], center[1] - radius, radius, radius))
        pygame.draw.rect(screen, GREEN, (center[0], center[1], radius, radius))
        pygame.draw.rect(screen, YELLOW, (center[0] - radius, center[1], radius, radius))

        pygame.draw.circle(screen, COLOR_WHITE, center, radius - 12)
        pygame.draw.rect(screen, BLUE, (center[0] - 2, center[1] - 4, radius - 5, 8))

    def draw_initial_state(self, screen, modal_y):
        center_x = SCREEN_WIDTH // 2

        if self.google_logo:
            logo_rect = self.google_logo.get_rect(center=(center_x, modal_y + 60))
            screen.blit(self.google_logo, logo_rect)
        else:
            self.draw_google_logo_fallback(screen, center_x - 20, modal_y + 40)

        title = FONT_LARGE.render("Sign in with Google", True, COLOR_BLACK)
        screen.blit(title, (center_x - title.get_width() // 2, modal_y + 100))

        subtitle = FONT_BODY.render("to continue to Health", True, GREY)
        screen.blit(subtitle, (center_x - subtitle.get_width() // 2, modal_y + 135))

        section_y = modal_y + 180
        choose_text = FONT_SMALL.render("Choose an account", True, GREY)
        screen.blit(choose_text, (20, section_y))

        self.account_buttons = []
        account_y = section_y + 30

        for i, account in enumerate(self.accounts):
            btn_rect = pygame.Rect(20, account_y, SCREEN_WIDTH - 40, 70)
            self.account_buttons.append((btn_rect, i))

            pygame.draw.rect(screen, LIGHT_GREY, btn_rect, border_radius=12)

            avatar_x = 55
            avatar_y = account_y + 35
            pygame.draw.circle(screen, account["avatar_color"], (avatar_x, avatar_y), 22)
            initial = account["name"][0].upper()
            initial_text = FONT_TITLE.render(initial, True, COLOR_WHITE)
            screen.blit(initial_text, (avatar_x - initial_text.get_width() // 2,
                                       avatar_y - initial_text.get_height() // 2))

            name_text = FONT_BODY.render(account["name"], True, COLOR_BLACK)
            screen.blit(name_text, (90, account_y + 15))
            email_text = FONT_SMALL.render(account["email"], True, GREY)
            screen.blit(email_text, (90, account_y + 40))

            account_y += 85

        self.another_account_y = account_y + 10
        another_text = FONT_BODY.render("Use another account", True, BLUE)
        screen.blit(another_text, (center_x - another_text.get_width() // 2, self.another_account_y))

        privacy_y = modal_y + self.modal_height - 60
        privacy1 = FONT_SMALL.render("To continue, Google will share your name,", True, GREY)
        privacy2 = FONT_SMALL.render("email, and profile picture with Health.", True, GREY)
        screen.blit(privacy1, (center_x - privacy1.get_width() // 2, privacy_y))
        screen.blit(privacy2, (center_x - privacy2.get_width() // 2, privacy_y + 18))

    def draw_accounts_state(self, screen, modal_y):
        self.draw_initial_state(screen, modal_y)

    def draw_loading_state(self, screen, modal_y):
        center_x = SCREEN_WIDTH // 2
        center_y = modal_y + 200

        colors = [BLUE, RED, YELLOW, GREEN]
        radius = 30

        for i, color in enumerate(colors):
            angle = (i * 90 + self.animation_progress * 8) * math.pi / 180
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            pygame.draw.circle(screen, color, (x, y), 8)

        if self.selected_account is not None:
            account = self.accounts[self.selected_account]
            text = FONT_BODY.render(f"Signing in as {account['email']}...", True, GREY)
            screen.blit(text, (center_x - text.get_width() // 2, modal_y + 300))

    def draw_success_state(self, screen, modal_y):
        center_x = SCREEN_WIDTH // 2
        center_y = modal_y + 200

        SUCCESS_GREEN = (52, 168, 83)
        circle_radius = min(45, int(self.success_progress * 0.9))
        pygame.draw.circle(screen, SUCCESS_GREEN, (center_x, center_y), circle_radius)

        if self.success_progress > 50:
            check_progress = min(1, (self.success_progress - 50) / 50)

            start1 = (center_x - 22, center_y)
            end1 = (center_x - 5, center_y + 18)
            current1 = (
                start1[0] + (end1[0] - start1[0]) * min(1, check_progress * 2),
                start1[1] + (end1[1] - start1[1]) * min(1, check_progress * 2)
            )
            pygame.draw.line(screen, COLOR_WHITE, start1, current1, 5)

            if check_progress > 0.5:
                start2 = (center_x - 5, center_y + 18)
                end2 = (center_x + 28, center_y - 18)
                progress2 = (check_progress - 0.5) * 2
                current2 = (
                    start2[0] + (end2[0] - start2[0]) * progress2,
                    start2[1] + (end2[1] - start2[1]) * progress2
                )
                pygame.draw.line(screen, COLOR_WHITE, start2, current2, 5)

        if self.selected_account is not None:
            account = self.accounts[self.selected_account]
            text = FONT_TITLE.render("Signed in!", True, COLOR_BLACK)
            screen.blit(text, (center_x - text.get_width() // 2, modal_y + 280))

            email_text = FONT_BODY.render(account["email"], True, GREY)
            screen.blit(email_text, (center_x - email_text.get_width() // 2, modal_y + 315))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            modal_y = SCREEN_HEIGHT - self.slide_progress
            if y < modal_y:
                return "cancel"

            if self.state == "initial" or self.state == "accounts":
                if hasattr(self, 'account_buttons'):
                    for btn_rect, account_idx in self.account_buttons:
                        if btn_rect.collidepoint(x, y):
                            self.selected_account = account_idx
                            self.state = "loading"
                            self.animation_progress = 0
                            return None

                if hasattr(self, 'another_account_y'):
                    if self.another_account_y < y < self.another_account_y + 30:
                        self.selected_account = 0
                        self.state = "loading"
                        return None

            if self.state == "success" and self.success_progress > 100:
                return "complete"

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "cancel"

        return None