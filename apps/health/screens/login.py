import pygame
import re
from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK
from apps.health.components import draw_button, draw_social_button, draw_input_field
from apps.shared import Database

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
RED = (255, 59, 48)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class LoginScreen:

    def __init__(self):
        self.db = Database()
        self.login_error = None
        self.email_text = ""
        self.password_text = ""
        self.active_input = None

        self.email_touched = False
        self.password_touched = False

        self.email_error_height = 0
        self.password_error_height = 0
        self.max_error_height = 18
        self.animation_speed = 2

        pygame.key.set_repeat(400, 50)

    def validate_email(self):
        if not self.email_touched:
            return None
        if not self.email_text:
            return "Email is required"
        if not EMAIL_PATTERN.match(self.email_text):
            return "Please enter a valid email address"
        return None

    def validate_password(self):
        if not self.password_touched:
            return None
        if len(self.password_text) < 8:
            return "Password must be at least 8 characters"
        return None

    def update_error_animations(self):
        email_error = self.validate_email()
        if email_error:
            self.email_error_height = min(self.email_error_height + self.animation_speed, self.max_error_height)
        else:
            self.email_error_height = max(self.email_error_height - self.animation_speed, 0)

        password_error = self.validate_password()
        if password_error:
            self.password_error_height = min(self.password_error_height + self.animation_speed, self.max_error_height)
        else:
            self.password_error_height = max(self.password_error_height - self.animation_speed, 0)

    def is_form_valid(self):
        return (
            EMAIL_PATTERN.match(self.email_text) and
            len(self.password_text) >= 8
        )

    def attempt_login(self):
        """Check the credentials against the database. Returns "main" or None."""
        self.email_touched = True
        self.password_touched = True

        if not self.is_form_valid():
            return None

        email = self.email_text.strip()
        patient = self.db.authenticate_patient(email, self.password_text)
        if patient is None:
            # Deliberately vague: saying which half was wrong tells an attacker
            # whether the address has an account
            self.login_error = "Incorrect email or password"
            self.password_text = ""
            return None

        self.login_error = None
        self.db.save_session("patient", patient.id, patient.email)
        return "main"

    def reset(self):
        self.email_text = ""
        self.password_text = ""
        self.active_input = None
        self.email_touched = False
        self.password_touched = False
        self.login_error = None

    def draw(self, screen):
        self.update_error_animations()

        screen.fill(COLOR_WHITE)

        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        title = FONT_TITLE.render("Sign In", True, COLOR_BLACK)
        screen.blit(title, (20, 100))

        subtitle = FONT_BODY.render("Welcome back to Health", True, GREY)
        screen.blit(subtitle, (20, 140))

        current_y = 200

        email_error = self.validate_email()
        draw_input_field(screen, "Email Address", self.email_text, 20, current_y,
                         SCREEN_WIDTH - 40, self.active_input == "email",
                         email_error, self.email_error_height)
        current_y += 50 + (self.email_error_height + 10 if self.email_error_height > 0 else 0) + 15

        password_error = self.validate_password()
        display_password = "•" * len(self.password_text)
        draw_input_field(screen, "Password", display_password, 20, current_y,
                         SCREEN_WIDTH - 40, self.active_input == "password",
                         password_error, self.password_error_height)
        current_y += 50 + (self.password_error_height + 10 if self.password_error_height > 0 else 0) + 10

        self.forgot_password_y = current_y
        forgot_text = FONT_SMALL.render("Forgot Password?", True, BLUE)
        self.forgot_password_x = SCREEN_WIDTH - forgot_text.get_width() - 20
        screen.blit(forgot_text, (self.forgot_password_x, current_y))
        current_y += 40

        if self.login_error:
            error_text = FONT_SMALL.render(self.login_error, True, RED)
            screen.blit(error_text, (20, current_y - 22))

        self.button_y = current_y
        button_color = BLUE if self.is_form_valid() else GREY
        draw_button(screen, "Sign In", 20, current_y, SCREEN_WIDTH - 40, 50, button_color)
        current_y += 70

        pygame.draw.line(screen, (220, 220, 220), (20, current_y), (SCREEN_WIDTH - 20, current_y))
        or_text = FONT_SMALL.render("or", True, GREY)
        or_bg = pygame.Rect(SCREEN_WIDTH // 2 - 20, current_y - 10, 40, 20)
        pygame.draw.rect(screen, COLOR_WHITE, or_bg)
        screen.blit(or_text, (SCREEN_WIDTH // 2 - or_text.get_width() // 2, current_y - 10))
        current_y += 30

        self.apple_button_y = current_y
        draw_social_button(screen, "Continue with Apple", 20, current_y, SCREEN_WIDTH - 40, 50, "apple")
        current_y += 65

        self.google_button_y = current_y
        draw_social_button(screen, "Continue with Google", 20, current_y, SCREEN_WIDTH - 40, 50, "google")
        current_y += 80

        self.signup_link_y = current_y
        no_account = FONT_SMALL.render("Don't have an account?", True, GREY)
        screen.blit(no_account, (SCREEN_WIDTH // 2 - 100, current_y))
        signup_link = FONT_SMALL.render("Sign Up", True, BLUE)
        screen.blit(signup_link, (SCREEN_WIDTH // 2 + 55, current_y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if x < 100 and 45 < y < 85:
                return "onboarding"

            current_y = 200

            email_area_end = current_y + 50 + (self.email_error_height + 10 if self.email_error_height > 0 else 0)
            if current_y < y < email_area_end:
                self.active_input = "email"
                self.email_touched = True
                return None
            current_y = email_area_end + 15

            password_area_end = current_y + 50 + (self.password_error_height + 10 if self.password_error_height > 0 else 0)
            if current_y < y < password_area_end:
                self.active_input = "password"
                self.password_touched = True
                return None

            if hasattr(self, 'forgot_password_y') and hasattr(self, 'forgot_password_x'):
                if self.forgot_password_y < y < self.forgot_password_y + 20 and x > self.forgot_password_x:
                    return "forgot_password"

            if hasattr(self, 'button_y') and self.button_y < y < self.button_y + 50:
                return self.attempt_login()

            if hasattr(self, 'apple_button_y') and self.apple_button_y < y < self.apple_button_y + 50:
                if 20 < x < SCREEN_WIDTH - 20:
                    return "apple_signin"

            if hasattr(self, 'google_button_y') and self.google_button_y < y < self.google_button_y + 50:
                if 20 < x < SCREEN_WIDTH - 20:
                    return "google_signin"

            if hasattr(self, 'signup_link_y') and self.signup_link_y < y < self.signup_link_y + 30:
                return "signup"

            if self.active_input == "email":
                self.email_touched = True
            elif self.active_input == "password":
                self.password_touched = True
            self.active_input = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "onboarding"
            elif event.key == pygame.K_RETURN:
                self.active_input = None
                return self.attempt_login()
            elif event.key == pygame.K_TAB:
                if self.active_input == "email":
                    self.email_touched = True
                    self.active_input = "password"
                    self.password_touched = True
                else:
                    if self.active_input == "password":
                        self.password_touched = True
                    self.active_input = "email"
                    self.email_touched = True
            elif self.active_input:
                if event.key == pygame.K_BACKSPACE:
                    if self.active_input == "email":
                        self.email_text = self.email_text[:-1]
                    else:
                        self.password_text = self.password_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    self.login_error = None
                    if self.active_input == "email":
                        self.email_text += event.unicode
                    else:
                        self.password_text += event.unicode

        return None