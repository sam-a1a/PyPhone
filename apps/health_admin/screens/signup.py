import pygame
import re
from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database, Doctor
from apps.shared.models import SPECIALTIES

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
RED = (255, 59, 48)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 12)
FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class AdminSignupScreen:
    def __init__(self):
        self.db = Database()
        self.name_text = ""
        self.email_text = ""
        self.password_text = ""
        self.specialty_text = ""
        self.active_input = None
        self.terms_accepted = False
        self.specialty_dropdown_open = False
        self.name_touched = False
        self.email_touched = False
        self.password_touched = False
        self.specialty_touched = False
        self.name_error_height = 0
        self.email_error_height = 0
        self.password_error_height = 0
        self.specialty_error_height = 0
        self.max_error_height = 18
        self.animation_speed = 2
        self.scroll_y = 0
        pygame.key.set_repeat(400, 50)

    def reset(self):
        self.name_text = ""
        self.email_text = ""
        self.password_text = ""
        self.specialty_text = ""
        self.active_input = None
        self.terms_accepted = False
        self.specialty_dropdown_open = False
        self.name_touched = False
        self.email_touched = False
        self.password_touched = False
        self.specialty_touched = False
        self.name_error_height = 0
        self.email_error_height = 0
        self.password_error_height = 0
        self.specialty_error_height = 0
        self.scroll_y = 0

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
        existing = self.db.get_doctor_by_email(self.email_text.strip())
        if existing:
            return "Email already registered"
        return None

    def validate_password(self):
        if not self.password_touched:
            return None
        if len(self.password_text) < 8:
            return "Password must be at least 8 characters"
        return None

    def validate_specialty(self):
        if not self.specialty_touched:
            return None
        if not self.specialty_text:
            return "Please select a specialty"
        return None

    def update_error_animations(self):
        if self.validate_name():
            self.name_error_height = min(self.name_error_height + self.animation_speed, self.max_error_height)
        else:
            self.name_error_height = max(self.name_error_height - self.animation_speed, 0)

        if self.validate_email():
            self.email_error_height = min(self.email_error_height + self.animation_speed, self.max_error_height)
        else:
            self.email_error_height = max(self.email_error_height - self.animation_speed, 0)

        if self.validate_password():
            self.password_error_height = min(self.password_error_height + self.animation_speed, self.max_error_height)
        else:
            self.password_error_height = max(self.password_error_height - self.animation_speed, 0)

        if self.validate_specialty():
            self.specialty_error_height = min(self.specialty_error_height + self.animation_speed, self.max_error_height)
        else:
            self.specialty_error_height = max(self.specialty_error_height - self.animation_speed, 0)

    def is_form_valid(self):
        return (
            len(self.name_text.strip()) >= 2 and
            EMAIL_PATTERN.match(self.email_text) and
            len(self.password_text) >= 8 and
            self.specialty_text and
            self.terms_accepted
        )

    def attempt_signup(self):
        self.name_touched = True
        self.email_touched = True
        self.password_touched = True
        self.specialty_touched = True

        if not self.is_form_valid():
            return None

        if self.db.get_doctor_by_email(self.email_text.strip()):
            return None

        doctors = self.db.get_all_doctors(active_only=False)
        doctor_number = f"DOC{len(doctors) + 1:03d}"

        doctor = Doctor(
            name=self.name_text.strip(),
            email=self.email_text.strip(),
            specialty=self.specialty_text,
            doctor_number=doctor_number,
            password_hash=self.db.hash_password(self.password_text)
        )

        doctor_id = self.db.add_doctor(doctor)
        self.db.save_session("doctor", doctor_id, self.email_text.strip())

        return "main"

    def draw(self, screen):
        self.update_error_animations()
        screen.fill(COLOR_WHITE)

        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        title = FONT_TITLE.render("Create Account", True, COLOR_BLACK)
        screen.blit(title, (20, 100))

        subtitle = FONT_BODY.render("Join as a medical professional", True, GREY)
        screen.blit(subtitle, (20, 140))

        current_y = 185

        name_error = self.validate_name()
        current_y = self.draw_input_field(
            screen, "Full Name (Dr.)", self.name_text,
            20, current_y, SCREEN_WIDTH - 40,
            self.active_input == "name",
            name_error, self.name_error_height
        )
        current_y += 12

        email_error = self.validate_email()
        current_y = self.draw_input_field(
            screen, "Email Address", self.email_text,
            20, current_y, SCREEN_WIDTH - 40,
            self.active_input == "email",
            email_error, self.email_error_height
        )
        current_y += 12

        password_error = self.validate_password()
        display_password = "•" * len(self.password_text)
        current_y = self.draw_input_field(
            screen, "Password", display_password,
            20, current_y, SCREEN_WIDTH - 40,
            self.active_input == "password",
            password_error, self.password_error_height
        )

        if len(self.password_text) < 8:
            hint_text = FONT_TINY.render("Must be at least 8 characters", True, GREY)
            screen.blit(hint_text, (20, current_y))
        current_y += 22

        specialty_error = self.validate_specialty()
        self.specialty_y = current_y
        current_y = self.draw_dropdown(
            screen, "Specialty", self.specialty_text,
            20, current_y, SCREEN_WIDTH - 40,
            self.specialty_dropdown_open,
            specialty_error, self.specialty_error_height
        )
        current_y += 15

        self.terms_y = current_y
        self.draw_checkbox(screen, 20, current_y, self.terms_accepted)
        terms_text = FONT_SMALL.render("I agree to the", True, COLOR_BLACK)
        screen.blit(terms_text, (50, current_y + 2))
        terms_link = FONT_SMALL.render("Terms of Service", True, BLUE)
        screen.blit(terms_link, (145, current_y + 2))
        current_y += 45

        self.button_y = current_y
        button_color = BLUE if self.is_form_valid() else GREY
        self.draw_button(screen, "Create Account", 20, current_y, SCREEN_WIDTH - 40, 50, button_color)
        current_y += 70

        pygame.draw.line(screen, (220, 220, 220), (20, current_y), (SCREEN_WIDTH - 20, current_y))
        or_text = FONT_SMALL.render("or", True, GREY)
        or_bg = pygame.Rect(SCREEN_WIDTH // 2 - 20, current_y - 10, 40, 20)
        pygame.draw.rect(screen, COLOR_WHITE, or_bg)
        screen.blit(or_text, (SCREEN_WIDTH // 2 - or_text.get_width() // 2, current_y - 10))
        current_y += 25

        self.apple_button_y = current_y
        self.draw_social_button(screen, "Continue with Apple", 20, current_y, SCREEN_WIDTH - 40, 50, "apple")
        current_y += 60

        self.google_button_y = current_y
        self.draw_social_button(screen, "Continue with Google", 20, current_y, SCREEN_WIDTH - 40, 50, "google")
        current_y += 65

        self.signin_link_y = current_y
        have_account = FONT_SMALL.render("Already have an account?", True, GREY)
        screen.blit(have_account, (SCREEN_WIDTH // 2 - 110, current_y))
        signin_link = FONT_SMALL.render("Sign In", True, BLUE)
        screen.blit(signin_link, (SCREEN_WIDTH // 2 + 60, current_y))

        if self.specialty_dropdown_open:
            self.draw_dropdown_options(screen, 20, self.specialty_y + 70, SCREEN_WIDTH - 40)

    def draw_input_field(self, screen, placeholder, value, x, y, width, is_active, error=None, error_height=0):
        field_height = 50

        if error and error_height > 0:
            border_color = RED
        elif is_active:
            border_color = BLUE
        else:
            border_color = (220, 220, 220)

        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, COLOR_WHITE, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)

        if value:
            text_surface = FONT_BODY.render(value, True, COLOR_BLACK)
            screen.blit(text_surface, (x + 15, y + (field_height - text_surface.get_height()) // 2))

            if is_active:
                cursor_x = x + 15 + text_surface.get_width() + 2
                pygame.draw.line(screen, COLOR_BLACK, (cursor_x, y + 12), (cursor_x, y + field_height - 12), 2)
        else:
            if is_active:
                pygame.draw.line(screen, COLOR_BLACK, (x + 15, y + 12), (x + 15, y + field_height - 12), 2)
            else:
                placeholder_surface = FONT_BODY.render(placeholder, True, (180, 180, 180))
                screen.blit(placeholder_surface, (x + 15, y + (field_height - placeholder_surface.get_height()) // 2))

        total_height = field_height
        if error and error_height > 0:
            error_font = pygame.font.SysFont("Arial", 12)
            error_surface = error_font.render(error, True, RED)
            error_y = y + field_height + 5

            if error_height >= error_surface.get_height():
                screen.blit(error_surface, (x + 5, error_y))
            else:
                clip_rect = pygame.Rect(0, 0, error_surface.get_width(), int(error_height))
                screen.blit(error_surface, (x + 5, error_y), clip_rect)

            total_height += error_height + 10

        return y + total_height

    def draw_dropdown(self, screen, placeholder, value, x, y, width, is_open, error=None, error_height=0):
        field_height = 50

        if error and error_height > 0:
            border_color = RED
        elif is_open:
            border_color = BLUE
        else:
            border_color = (220, 220, 220)

        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, COLOR_WHITE, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)

        if value:
            text_surface = FONT_BODY.render(value, True, COLOR_BLACK)
        else:
            text_surface = FONT_BODY.render(placeholder, True, (180, 180, 180))

        screen.blit(text_surface, (x + 15, y + (field_height - text_surface.get_height()) // 2))

        arrow = "▼" if not is_open else "▲"
        arrow_surface = FONT_BODY.render(arrow, True, GREY)
        screen.blit(arrow_surface, (x + width - 30, y + (field_height - arrow_surface.get_height()) // 2))

        total_height = field_height
        if error and error_height > 0 and not is_open:
            error_font = pygame.font.SysFont("Arial", 12)
            error_surface = error_font.render(error, True, RED)
            error_y = y + field_height + 5

            if error_height >= error_surface.get_height():
                screen.blit(error_surface, (x + 5, error_y))
            else:
                clip_rect = pygame.Rect(0, 0, error_surface.get_width(), int(error_height))
                screen.blit(error_surface, (x + 5, error_y), clip_rect)

            total_height += error_height + 10

        return y + total_height

    def draw_dropdown_options(self, screen, x, y, width):
        visible_options = SPECIALTIES[:6]
        option_height = 44
        dropdown_height = len(visible_options) * option_height

        shadow_rect = pygame.Rect(x + 3, y + 3, width, dropdown_height)
        pygame.draw.rect(screen, (200, 200, 200), shadow_rect, border_radius=12)

        dropdown_rect = pygame.Rect(x, y, width, dropdown_height)
        pygame.draw.rect(screen, COLOR_WHITE, dropdown_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), dropdown_rect, 1, border_radius=12)

        self.option_rects = []
        for i, option in enumerate(visible_options):
            option_y = y + (i * option_height)
            option_rect = pygame.Rect(x, option_y, width, option_height)
            self.option_rects.append((option_rect, option))

            if option == self.specialty_text:
                highlight = pygame.Surface((width - 8, option_height - 8), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (0, 122, 255, 30), (0, 0, width - 8, option_height - 8), border_radius=8)
                screen.blit(highlight, (x + 4, option_y + 4))

            option_surface = FONT_BODY.render(option, True, COLOR_BLACK)
            screen.blit(option_surface, (x + 15, option_y + (option_height - option_surface.get_height()) // 2))

            if i < len(visible_options) - 1:
                pygame.draw.line(screen, (240, 240, 240), (x + 15, option_y + option_height),
                               (x + width - 15, option_y + option_height), 1)

    def draw_checkbox(self, screen, x, y, checked):
        box_size = 24
        box_rect = pygame.Rect(x, y, box_size, box_size)

        if checked:
            pygame.draw.rect(screen, BLUE, box_rect, border_radius=6)
            pygame.draw.line(screen, COLOR_WHITE, (x + 6, y + 12), (x + 10, y + 17), 2)
            pygame.draw.line(screen, COLOR_WHITE, (x + 10, y + 17), (x + 18, y + 7), 2)
        else:
            pygame.draw.rect(screen, COLOR_WHITE, box_rect, border_radius=6)
            pygame.draw.rect(screen, (200, 200, 200), box_rect, 2, border_radius=6)

    def draw_button(self, screen, text, x, y, width, height, color):
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, color, button_rect, border_radius=12)

        text_surface = FONT_BUTTON.render(text, True, COLOR_WHITE)
        text_x = x + (width - text_surface.get_width()) // 2
        text_y = y + (height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

    def draw_social_button(self, screen, text, x, y, width, height, provider):
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLOR_WHITE, button_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), button_rect, 1, border_radius=12)

        icon_size = 24
        text_surface = FONT_BODY.render(text, True, COLOR_BLACK)
        total_width = icon_size + 10 + text_surface.get_width()
        start_x = x + (width - total_width) // 2

        icon_x = start_x + icon_size // 2
        icon_y = y + height // 2
        if provider == "apple":
            pygame.draw.circle(screen, COLOR_BLACK, (icon_x, icon_y), 12)
        elif provider == "google":
            pygame.draw.circle(screen, (234, 67, 53), (icon_x, icon_y), 12)

        text_x = start_x + icon_size + 10
        text_y = y + (height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if self.specialty_dropdown_open and hasattr(self, 'option_rects'):
                for option_rect, option_value in self.option_rects:
                    if option_rect.collidepoint(x, y):
                        self.specialty_text = option_value
                        self.specialty_dropdown_open = False
                        self.specialty_touched = True
                        return None

            if self.specialty_dropdown_open:
                self.specialty_dropdown_open = False
                return None

            if x < 100 and 45 < y < 85:
                self.reset()
                return "login"

            current_y = 185

            name_area_end = current_y + 50 + (self.name_error_height + 10 if self.name_error_height > 0 else 0)
            if current_y < y < name_area_end:
                self.active_input = "name"
                self.name_touched = True
                return None
            current_y = name_area_end + 12

            email_area_end = current_y + 50 + (self.email_error_height + 10 if self.email_error_height > 0 else 0)
            if current_y < y < email_area_end:
                self.active_input = "email"
                self.email_touched = True
                return None
            current_y = email_area_end + 12

            password_area_end = current_y + 50 + (self.password_error_height + 10 if self.password_error_height > 0 else 0)
            if current_y < y < password_area_end:
                self.active_input = "password"
                self.password_touched = True
                return None
            current_y = password_area_end + 22

            if hasattr(self, 'specialty_y') and self.specialty_y < y < self.specialty_y + 50:
                self.specialty_dropdown_open = not self.specialty_dropdown_open
                self.specialty_touched = True
                self.active_input = None
                return None

            if hasattr(self, 'terms_y') and self.terms_y < y < self.terms_y + 30 and 20 < x < 50:
                self.terms_accepted = not self.terms_accepted
                return None

            if hasattr(self, 'terms_y') and self.terms_y < y < self.terms_y + 25 and 145 < x < 280:
                return "terms"

            if hasattr(self, 'button_y') and self.button_y < y < self.button_y + 50:
                return self.attempt_signup()

            if hasattr(self, 'apple_button_y') and self.apple_button_y < y < self.apple_button_y + 50:
                return "apple_signin"

            if hasattr(self, 'google_button_y') and self.google_button_y < y < self.google_button_y + 50:
                return "google_signin"

            if hasattr(self, 'signin_link_y') and self.signin_link_y < y < self.signin_link_y + 30:
                self.reset()
                return "login"

            self.active_input = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.reset()
                return "login"
            elif event.key == pygame.K_RETURN:
                return self.attempt_signup()
            elif event.key == pygame.K_TAB:
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
                    elif self.active_input == "password":
                        self.password_text = self.password_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if self.active_input == "name":
                        self.name_text += event.unicode
                    elif self.active_input == "email":
                        self.email_text += event.unicode
                    elif self.active_input == "password":
                        self.password_text += event.unicode

        return None