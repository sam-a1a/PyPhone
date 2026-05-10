import pygame
import re
from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK
from apps.health.components import draw_button, draw_input_field

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
GREEN = (52, 199, 89)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class ForgotPasswordScreen:

    def __init__(self):
        self.email_text = ""
        self.active_input = None
        self.email_touched = False

        self.email_error_height = 0
        self.max_error_height = 18
        self.animation_speed = 2

        self.email_sent = False
        self.success_message_alpha = 0

        pygame.key.set_repeat(400, 50)

    def reset(self):
        self.email_text = ""
        self.active_input = None
        self.email_touched = False
        self.email_error_height = 0
        self.email_sent = False
        self.success_message_alpha = 0

    def validate_email(self):
        if not self.email_touched:
            return None
        if not self.email_text:
            return "Email is required"
        if not EMAIL_PATTERN.match(self.email_text):
            return "Please enter a valid email address"
        return None

    def is_email_valid(self):
        return EMAIL_PATTERN.match(self.email_text) is not None

    def update_animations(self):
        email_error = self.validate_email()
        if email_error:
            self.email_error_height = min(self.email_error_height + self.animation_speed, self.max_error_height)
        else:
            self.email_error_height = max(self.email_error_height - self.animation_speed, 0)

        if self.email_sent:
            self.success_message_alpha = min(self.success_message_alpha + 10, 255)

    def draw(self, screen):
        self.update_animations()

        screen.fill(COLOR_WHITE)

        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        if not self.email_sent:
            self.draw_request_form(screen)
        else:
            self.draw_success_message(screen)

    def draw_request_form(self, screen):
        title = FONT_TITLE.render("Reset Password", True, COLOR_BLACK)
        screen.blit(title, (20, 100))

        desc_lines = [
            "Enter the email address associated",
            "with your account and we'll send you",
            "a link to reset your password."
        ]
        y = 150
        for line in desc_lines:
            desc_text = FONT_BODY.render(line, True, GREY)
            screen.blit(desc_text, (20, y))
            y += 24

        current_y = 250
        email_error = self.validate_email()
        draw_input_field(screen, "Email Address", self.email_text, 20, current_y,
                         SCREEN_WIDTH - 40, self.active_input == "email",
                         email_error, self.email_error_height)
        current_y += 50 + (self.email_error_height + 10 if self.email_error_height > 0 else 0) + 30

        self.button_y = current_y
        button_color = BLUE if self.is_email_valid() else GREY
        draw_button(screen, "Send Reset Link", 20, current_y, SCREEN_WIDTH - 40, 50, button_color)
        current_y += 80

    def draw_success_message(self, screen):
        center_x = SCREEN_WIDTH // 2
        center_y = 200

        circle_surface = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (*GREEN, self.success_message_alpha), (60, 60), 60)
        screen.blit(circle_surface, (center_x - 60, center_y - 60))

        if self.success_message_alpha > 100:
            check_alpha = min(255, (self.success_message_alpha - 100) * 3)
            check_surface = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.line(check_surface, (255, 255, 255, check_alpha),
                           (35, 60), (55, 80), 5)
            pygame.draw.line(check_surface, (255, 255, 255, check_alpha),
                           (55, 80), (85, 40), 5)
            screen.blit(check_surface, (center_x - 60, center_y - 60))

        title = FONT_TITLE.render("Check Your Email", True, COLOR_BLACK)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(title, (title_x, 300))

        desc_lines = [
            f"We've sent a password reset link to:",
            "",
            self.email_text,
            "",
            "Please check your inbox and follow",
            "the instructions to reset your password."
        ]
        y = 350
        for line in desc_lines:
            if line == self.email_text:
                desc_text = FONT_BODY.render(line, True, BLUE)
            else:
                desc_text = FONT_BODY.render(line, True, GREY)
            text_x = (SCREEN_WIDTH - desc_text.get_width()) // 2
            screen.blit(desc_text, (text_x, y))
            y += 26

        y += 30
        didnt_receive = FONT_SMALL.render("Didn't receive the email?", True, GREY)
        screen.blit(didnt_receive, (SCREEN_WIDTH // 2 - didnt_receive.get_width() // 2, y))

        y += 25
        self.resend_y = y
        resend_link = FONT_SMALL.render("Resend", True, BLUE)
        screen.blit(resend_link, (SCREEN_WIDTH // 2 - resend_link.get_width() // 2, y))

        self.back_button_y = 650
        draw_button(screen, "Back to Sign In", 20, self.back_button_y, SCREEN_WIDTH - 40, 50, BLUE)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if x < 100 and 45 < y < 85:
                self.reset()
                return "login"

            if not self.email_sent:
                if 250 < y < 320:
                    self.active_input = "email"
                    self.email_touched = True
                    return None

                if hasattr(self, 'button_y') and self.button_y < y < self.button_y + 50:
                    if self.is_email_valid():
                        self.email_sent = True
                    else:
                        self.email_touched = True
                    return None

                if hasattr(self, 'signin_link_y') and self.signin_link_y < y < self.signin_link_y + 30:
                    self.reset()
                    return "login"

                if self.active_input == "email":
                    self.email_touched = True
                self.active_input = None

            else:
                if hasattr(self, 'resend_y') and self.resend_y < y < self.resend_y + 25:
                    self.success_message_alpha = 0
                    return None

                if hasattr(self, 'back_button_y') and self.back_button_y < y < self.back_button_y + 50:
                    self.reset()
                    return "login"

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.reset()
                return "login"
            elif event.key == pygame.K_RETURN:
                if not self.email_sent:
                    if self.is_email_valid():
                        self.email_sent = True
                    else:
                        self.email_touched = True
                else:
                    self.reset()
                    return "login"
                self.active_input = None
            elif self.active_input == "email" and not self.email_sent:
                if event.key == pygame.K_BACKSPACE:
                    self.email_text = self.email_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    self.email_text += event.unicode

        return None