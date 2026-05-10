import pygame
import os
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
LIGHT_GREY = (245, 245, 247)

FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_LARGE = pygame.font.SysFont("Arial", 24, bold=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")


class AppleSignInModal:

    def __init__(self):
        self.state = "initial"
        self.animation_progress = 0
        self.slide_progress = 0
        self.face_id_progress = 0
        self.success_progress = 0
        self.modal_height = 400
        self.user_email = "bassam@icloud.com"
        self.masked_email = "b***m@icloud.com"

        self.apple_logo = None
        self.load_apple_logo()

        self.slide_speed = 30
        self.face_id_speed = 3

    def load_apple_logo(self):
        logo_path = os.path.join(ICON_DIR, "apple.png")
        if os.path.exists(logo_path):
            try:
                self.apple_logo = pygame.image.load(logo_path).convert_alpha()
                self.apple_logo = pygame.transform.smoothscale(self.apple_logo, (60, 60))
            except (pygame.error, OSError):
                pass

    def reset(self):
        self.state = "initial"
        self.animation_progress = 0
        self.slide_progress = 0
        self.face_id_progress = 0
        self.success_progress = 0

    def update(self):
        if self.slide_progress < self.modal_height:
            self.slide_progress = min(self.slide_progress + self.slide_speed, self.modal_height)

        if self.state == "face_id":
            self.face_id_progress += self.face_id_speed
            if self.face_id_progress >= 100:
                self.state = "loading"
                self.animation_progress = 0

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
        elif self.state == "face_id":
            self.draw_face_id_state(screen, modal_y)
        elif self.state == "loading":
            self.draw_loading_state(screen, modal_y)
        elif self.state == "success":
            self.draw_success_state(screen, modal_y)

    def draw_initial_state(self, screen, modal_y):
        center_x = SCREEN_WIDTH // 2

        if self.apple_logo:
            logo_rect = self.apple_logo.get_rect(center=(center_x, modal_y + 60))
            screen.blit(self.apple_logo, logo_rect)
        else:
            pygame.draw.circle(screen, COLOR_BLACK, (center_x, modal_y + 60), 30)

        title = FONT_LARGE.render("Sign in with Apple", True, COLOR_BLACK)
        screen.blit(title, (center_x - title.get_width() // 2, modal_y + 105))

        app_text = FONT_BODY.render("Health wants to use", True, GREY)
        screen.blit(app_text, (center_x - app_text.get_width() // 2, modal_y + 150))

        apple_id_text = FONT_BODY.render("your Apple ID", True, GREY)
        screen.blit(apple_id_text, (center_x - apple_id_text.get_width() // 2, modal_y + 175))

        email_y = modal_y + 215
        pygame.draw.rect(screen, LIGHT_GREY, (20, email_y, SCREEN_WIDTH - 40, 50), border_radius=10)
        email_text = FONT_BODY.render(self.masked_email, True, COLOR_BLACK)
        screen.blit(email_text, (40, email_y + 15))

        privacy_text = FONT_SMALL.render("Your email will be shared with this app.", True, GREY)
        screen.blit(privacy_text, (center_x - privacy_text.get_width() // 2, modal_y + 285))

        self.continue_button_y = modal_y + 325
        pygame.draw.rect(screen, COLOR_BLACK, (20, self.continue_button_y, SCREEN_WIDTH - 40, 50), border_radius=12)
        continue_text = FONT_TITLE.render("Continue", True, COLOR_WHITE)
        screen.blit(continue_text, (center_x - continue_text.get_width() // 2, self.continue_button_y + 13))

    def draw_face_id_state(self, screen, modal_y):
        center_x = SCREEN_WIDTH // 2
        center_y = modal_y + 160

        face_size = 80
        face_rect = pygame.Rect(center_x - face_size // 2, center_y - face_size // 2, face_size, face_size)

        pygame.draw.rect(screen, BLUE, face_rect, 3, border_radius=20)

        eye_y = center_y - 10
        pygame.draw.circle(screen, BLUE, (center_x - 15, eye_y), 5)
        pygame.draw.circle(screen, BLUE, (center_x + 15, eye_y), 5)

        scan_y = center_y - 30 + int((self.face_id_progress / 100) * 60)
        pygame.draw.line(screen, (0, 200, 255), (center_x - 35, scan_y), (center_x + 35, scan_y), 2)

        text = FONT_TITLE.render("Face ID", True, COLOR_BLACK)
        screen.blit(text, (center_x - text.get_width() // 2, modal_y + 260))

        desc = FONT_BODY.render("Look at your iPhone to authenticate", True, GREY)
        screen.blit(desc, (center_x - desc.get_width() // 2, modal_y + 295))

    def draw_loading_state(self, screen, modal_y):
        center_x = SCREEN_WIDTH // 2
        center_y = modal_y + 160

        radius = 25
        for i in range(8):
            angle = (i * 45 + self.animation_progress * 5) * math.pi / 180
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            alpha = 255 - (i * 30)
            color = (0, 0, 0, max(50, alpha))
            dot_surface = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, color, (6, 6), 6)
            screen.blit(dot_surface, (x - 6, y - 6))

        text = FONT_BODY.render("Signing in...", True, GREY)
        screen.blit(text, (center_x - text.get_width() // 2, modal_y + 260))

    def draw_success_state(self, screen, modal_y):
        center_x = SCREEN_WIDTH // 2
        center_y = modal_y + 160

        GREEN = (52, 199, 89)
        circle_radius = min(40, int(self.success_progress * 0.8))
        pygame.draw.circle(screen, GREEN, (center_x, center_y), circle_radius)

        if self.success_progress > 50:
            check_progress = min(1, (self.success_progress - 50) / 50)

            start1 = (center_x - 20, center_y)
            end1 = (center_x - 5, center_y + 15)
            current1 = (
                start1[0] + (end1[0] - start1[0]) * min(1, check_progress * 2),
                start1[1] + (end1[1] - start1[1]) * min(1, check_progress * 2)
            )
            pygame.draw.line(screen, COLOR_WHITE, start1, current1, 4)

            if check_progress > 0.5:
                start2 = (center_x - 5, center_y + 15)
                end2 = (center_x + 25, center_y - 15)
                progress2 = (check_progress - 0.5) * 2
                current2 = (
                    start2[0] + (end2[0] - start2[0]) * progress2,
                    start2[1] + (end2[1] - start2[1]) * progress2
                )
                pygame.draw.line(screen, COLOR_WHITE, start2, current2, 4)

        text = FONT_TITLE.render("Signed In", True, COLOR_BLACK)
        screen.blit(text, (center_x - text.get_width() // 2, modal_y + 260))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            modal_y = SCREEN_HEIGHT - self.slide_progress
            if y < modal_y:
                return "cancel"

            if self.state == "initial":
                if hasattr(self, 'continue_button_y'):
                    if self.continue_button_y < y < self.continue_button_y + 50 and 20 < x < SCREEN_WIDTH - 20:
                        self.state = "face_id"
                        return None

            if self.state == "success" and self.success_progress > 100:
                return "complete"

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "cancel"
            elif event.key == pygame.K_RETURN and self.state == "initial":
                self.state = "face_id"

        return None