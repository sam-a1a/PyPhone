import pygame
import re
from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK
from apps.health.components import draw_button, draw_social_button, draw_input_field, draw_checkbox

BLUE = (0, 122, 255)
GREY = (142, 142, 147)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 12)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class SignupScreen:

    def __init__(self):
        self.name_text = ""
        self.email_text = ""
        self.password_text = ""
        self.active_input = None
        self.terms_accepted = False

        self.name_touched = False
        self.email_touched = False
        self.password_touched = False

        self.name_error_height = 0
        self.email_error_height = 0
        self.password_error_height = 0
        self.max_error_height = 18
        self.animation_speed = 2

        pygame.key.set_repeat(400, 50)

    def validate_name(self):
        if not self.name_touched:
            return None
        if len(self.name_text.strip()) < 2:
            return "Name must be at least 2 characters"
        return None

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
        name_error = self.validate_name()
        if name_error:
            self.name_error_height = min(self.name_error_height + self.animation_speed, self.max_error_height)
        else:
            self.name_error_height = max(self.name_error_height - self.animation_speed, 0)

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
            len(self.name_text.strip()) >= 2 and
            EMAIL_PATTERN.match(self.email_text) and
            len(self.password_text) >= 8 and
            self.terms_accepted
        )

    def draw(self, screen):
        self.update_error_animations()

        screen.fill(COLOR_WHITE)

        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        title = FONT_TITLE.render("Create Account", True, COLOR_BLACK)
        screen.blit(title, (20, 100))

        subtitle = FONT_BODY.render("Start your health journey today", True, GREY)
        screen.blit(subtitle, (20, 140))

        current_y = 190

        name_error = self.validate_name()
        draw_input_field(screen, "Full Name", self.name_text, 20, current_y,
                         SCREEN_WIDTH - 40, self.active_input == "name",
                         name_error, self.name_error_height)
        current_y += 50 + (self.name_error_height + 10 if self.name_error_height > 0 else 0) + 15

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

        if len(self.password_text) < 8:
            req_text = FONT_TINY.render("Must be at least 8 characters", True, GREY)
            screen.blit(req_text, (20, current_y))
        current_y += 25

        draw_checkbox(screen, 20, current_y, self.terms_accepted)
        terms_text = FONT_SMALL.render("I agree to the", True, COLOR_BLACK)
        screen.blit(terms_text, (50, current_y))
        terms_link = FONT_SMALL.render("Terms of Service", True, BLUE)
        screen.blit(terms_link, (145, current_y))
        and_text = FONT_SMALL.render("and", True, COLOR_BLACK)
        screen.blit(and_text, (50, current_y + 20))
        privacy_link = FONT_SMALL.render("Privacy Policy", True, BLUE)
        screen.blit(privacy_link, (80, current_y + 20))
        self.terms_y = current_y
        current_y += 55

        self.button_y = current_y

        button_color = BLUE if self.is_form_valid() else GREY
        draw_button(screen, "Create Account", 20, current_y, SCREEN_WIDTH - 40, 50, button_color)
        current_y += 70

        pygame.draw.line(screen, (220, 220, 220), (20, current_y), (SCREEN_WIDTH - 20, current_y))
        or_text = FONT_SMALL.render("or", True, GREY)
        or_bg = pygame.Rect(SCREEN_WIDTH // 2 - 20, current_y - 10, 40, 20)
        pygame.draw.rect(screen, COLOR_WHITE, or_bg)
        screen.blit(or_text, (SCREEN_WIDTH // 2 - or_text.get_width() // 2, current_y - 10))
        current_y += 30

        draw_social_button(screen, "Continue with Apple", 20, current_y, SCREEN_WIDTH - 40, 50, "apple")
        current_y += 65
        draw_social_button(screen, "Continue with Google", 20, current_y, SCREEN_WIDTH - 40, 50, "google")
        current_y += 70

        self.signin_link_y = current_y
        have_account = FONT_SMALL.render("Already have an account?", True, GREY)
        screen.blit(have_account, (SCREEN_WIDTH // 2 - 110, current_y))
        signin_link = FONT_SMALL.render("Sign In", True, BLUE)
        screen.blit(signin_link, (SCREEN_WIDTH // 2 + 60, current_y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if 15 < x < 80 and 50 < y < 80:
                return "login"

            current_y = 190

            name_area_end = current_y + 50 + (self.name_error_height + 10 if self.name_error_height > 0 else 0)
            if current_y < y < name_area_end:
                self.active_input = "name"
                self.name_touched = True
                return None
            current_y = name_area_end + 15

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

            if hasattr(self, 'terms_y') and self.terms_y < y < self.terms_y + 30 and 20 < x < 50:
                self.terms_accepted = not self.terms_accepted
                return None

            if hasattr(self, 'terms_y') and self.terms_y < y < self.terms_y + 20 and 145 < x < 270:
                return "terms"

            if hasattr(self, 'button_y') and self.button_y < y < self.button_y + 50:
                if self.is_form_valid():
                    return "main"
                else:
                    self.name_touched = True
                    self.email_touched = True
                    self.password_touched = True
                return None

            if hasattr(self, 'signin_link_y') and self.signin_link_y < y < self.signin_link_y + 30:
                return "login"

            if self.active_input == "name":
                self.name_touched = True
            elif self.active_input == "email":
                self.email_touched = True
            elif self.active_input == "password":
                self.password_touched = True
            self.active_input = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "login"
            elif event.key == pygame.K_RETURN:
                if self.is_form_valid():
                    return "main"
                else:
                    self.name_touched = True
                    self.email_touched = True
                    self.password_touched = True
                self.active_input = None
            elif event.key == pygame.K_TAB:
                if self.active_input == "name":
                    self.name_touched = True
                elif self.active_input == "email":
                    self.email_touched = True
                elif self.active_input == "password":
                    self.password_touched = True

                inputs = ["name", "email", "password"]
                if self.active_input in inputs:
                    idx = inputs.index(self.active_input)
                    self.active_input = inputs[(idx + 1) % len(inputs)]
                else:
                    self.active_input = "name"

                if self.active_input == "name":
                    self.name_touched = True
                elif self.active_input == "email":
                    self.email_touched = True
                elif self.active_input == "password":
                    self.password_touched = True

            elif self.active_input:
                if event.key == pygame.K_BACKSPACE:
                    if self.active_input == "name":
                        self.name_text = self.name_text[:-1]
                    elif self.active_input == "email":
                        self.email_text = self.email_text[:-1]
                    else:
                        self.password_text = self.password_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if self.active_input == "name":
                        self.name_text += event.unicode
                    elif self.active_input == "email":
                        self.email_text += event.unicode
                    else:
                        self.password_text += event.unicode

        return None