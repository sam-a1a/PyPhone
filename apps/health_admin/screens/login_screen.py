import pygame
import re
import os
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
RED = (255, 59, 48)
GREEN = (52, 199, 89)

FONT_LARGE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 11)
FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")


class AdminLoginScreen:

    def __init__(self):
        self.db = Database()

        # Form state
        self.email_text = ""
        self.password_text = ""
        self.active_input = None

        # Validation state
        self.email_touched = False
        self.password_touched = False

        # Error animation
        self.email_error_height = 0
        self.password_error_height = 0
        self.max_error_height = 18
        self.animation_speed = 2

        # Global error (invalid credentials)
        self.global_error = None

        # Login result info
        self.login_type = None  # Will be "admin" or "doctor" after successful login

        # Social icon cache
        self._social_icon_cache = {}

        # Key repeat
        pygame.key.set_repeat(400, 50)

    def reset(self):
        """Reset screen state."""
        self.email_text = ""
        self.password_text = ""
        self.active_input = None
        self.email_touched = False
        self.password_touched = False
        self.email_error_height = 0
        self.password_error_height = 0
        self.global_error = None
        self.login_type = None

    def load_social_icon(self, provider, size=24):
        """Load social provider icon."""
        cache_key = f"{provider}_{size}"
        if cache_key in self._social_icon_cache:
            return self._social_icon_cache[cache_key]

        icon_path = os.path.join(ICON_DIR, f"{provider}.png")
        if os.path.exists(icon_path):
            try:
                icon = pygame.image.load(icon_path).convert_alpha()
                icon = pygame.transform.smoothscale(icon, (size, size))
                self._social_icon_cache[cache_key] = icon
                return icon
            except (pygame.error, OSError):
                pass
        return None

    def validate_email(self):
        """Validate email field."""
        if not self.email_touched:
            return None
        if not self.email_text:
            return "Email is required"
        if not EMAIL_PATTERN.match(self.email_text):
            return "Please enter a valid email address"
        return None

    def validate_password(self):
        """Validate password field."""
        if not self.password_touched:
            return None
        if len(self.password_text) < 8:
            return "Password must be at least 8 characters"
        return None

    def update_error_animations(self):
        """Update error label animations."""
        email_error = self.validate_email()
        if email_error:
            self.email_error_height = min(self.email_error_height + self.animation_speed, self.max_error_height)
        else:
            self.email_error_height = max(self.email_error_height - self.animation_speed, 0)

        password_error = self.validate_password() or self.global_error
        if password_error:
            self.password_error_height = min(self.password_error_height + self.animation_speed, self.max_error_height)
        else:
            self.password_error_height = max(self.password_error_height - self.animation_speed, 0)

    def is_form_valid(self):
        """Check if form is valid."""
        return (
            EMAIL_PATTERN.match(self.email_text) and
            len(self.password_text) >= 8
        )

    def attempt_login(self):
        """Attempt to login as admin first, then as doctor."""
        self.email_touched = True
        self.password_touched = True
        self.global_error = None

        if not self.is_form_valid():
            return None

        email = self.email_text.strip()
        password = self.password_text

        # Try admin authentication first
        admin = self.db.authenticate_admin(email, password)
        if admin:
            self.db.save_session("admin", admin.id, admin.email)
            self.login_type = "admin"
            return "admin_main"

        # Try doctor authentication
        doctor = self.db.authenticate_doctor(email, password)
        if doctor:
            self.db.save_session("doctor", doctor.id, doctor.email)
            self.login_type = "doctor"
            return "doctor_main"

        # Neither worked
        self.global_error = "Invalid email or password"
        return None

    def draw(self, screen):
        """Draw the login screen."""
        self.update_error_animations()

        screen.fill(COLOR_WHITE)

        # Back button
        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        # Title
        title = FONT_LARGE.render("Admin Portal", True, COLOR_BLACK)
        screen.blit(title, (20, 100))

        # Subtitle
        subtitle = FONT_BODY.render("Sign in as Admin or Doctor", True, GREY)
        screen.blit(subtitle, (20, 138))

        current_y = 190

        # Email input
        email_error = self.validate_email()
        current_y = self.draw_input_field(
            screen, "Email Address", self.email_text,
            20, current_y, SCREEN_WIDTH - 40,
            self.active_input == "email",
            email_error, self.email_error_height
        )
        current_y += 15

        # Password input
        password_error = self.validate_password() or self.global_error
        display_password = "•" * len(self.password_text)
        current_y = self.draw_input_field(
            screen, "Password", display_password,
            20, current_y, SCREEN_WIDTH - 40,
            self.active_input == "password",
            password_error, self.password_error_height
        )
        current_y += 10

        # Forgot Password link
        self.forgot_password_y = current_y
        forgot_text = FONT_SMALL.render("Forgot Password?", True, BLUE)
        self.forgot_password_x = SCREEN_WIDTH - forgot_text.get_width() - 20
        screen.blit(forgot_text, (self.forgot_password_x, current_y))
        current_y += 40

        # Sign In button
        self.button_y = current_y
        button_color = BLUE if self.is_form_valid() else GREY
        self.draw_button(screen, "Sign In", 20, current_y, SCREEN_WIDTH - 40, 50, button_color)
        current_y += 70

        # Divider
        pygame.draw.line(screen, (220, 220, 220), (20, current_y), (SCREEN_WIDTH - 20, current_y))
        or_text = FONT_SMALL.render("or", True, GREY)
        or_bg = pygame.Rect(SCREEN_WIDTH // 2 - 20, current_y - 10, 40, 20)
        pygame.draw.rect(screen, COLOR_WHITE, or_bg)
        screen.blit(or_text, (SCREEN_WIDTH // 2 - or_text.get_width() // 2, current_y - 10))
        current_y += 30

        # Apple Sign In
        self.apple_button_y = current_y
        self.draw_social_button(screen, "Continue with Apple", 20, current_y, SCREEN_WIDTH - 40, 50, "apple")
        current_y += 65

        # Google Sign In
        self.google_button_y = current_y
        self.draw_social_button(screen, "Continue with Google", 20, current_y, SCREEN_WIDTH - 40, 50, "google")
        current_y += 80

        # Sign up link
        self.signup_link_y = current_y
        no_account = FONT_SMALL.render("New doctor?", True, GREY)
        screen.blit(no_account, (SCREEN_WIDTH // 2 - 80, current_y))
        signup_link = FONT_SMALL.render("Register", True, BLUE)
        screen.blit(signup_link, (SCREEN_WIDTH // 2 + 20, current_y))

        # Demo hints at bottom
        self.draw_demo_hints(screen)

    def draw_demo_hints(self, screen):
        """Draw demo login hints at bottom."""
        hint_y = SCREEN_HEIGHT - 85

        # Admin hint
        admin_hint = FONT_TINY.render("Admin: admin@admin.com / adminadmin", True, (180, 180, 180))
        hint_x = (SCREEN_WIDTH - admin_hint.get_width()) // 2
        screen.blit(admin_hint, (hint_x, hint_y))

        # Doctor hint
        doctor_hint = FONT_TINY.render("Doctor: jihan@demo.com / jihanjihan", True, (180, 180, 180))
        hint_x = (SCREEN_WIDTH - doctor_hint.get_width()) // 2
        screen.blit(doctor_hint, (hint_x, hint_y + 18))

    def draw_input_field(self, screen, placeholder, value, x, y, width, is_active, error=None, error_height=0):
        """Draw an input field matching Health app style."""
        field_height = 50

        # Border color
        if error and error_height > 0:
            border_color = RED
        elif is_active:
            border_color = BLUE
        else:
            border_color = (220, 220, 220)

        # Input box
        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, COLOR_WHITE, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)

        # Value or placeholder
        if value:
            text_surface = FONT_BODY.render(value, True, COLOR_BLACK)
            screen.blit(text_surface, (x + 15, y + (field_height - text_surface.get_height()) // 2))

            # Cursor
            if is_active:
                cursor_x = x + 15 + text_surface.get_width() + 2
                pygame.draw.line(screen, COLOR_BLACK, (cursor_x, y + 12), (cursor_x, y + field_height - 12), 2)
        else:
            if is_active:
                pygame.draw.line(screen, COLOR_BLACK, (x + 15, y + 12), (x + 15, y + field_height - 12), 2)
            else:
                placeholder_surface = FONT_BODY.render(placeholder, True, (180, 180, 180))
                screen.blit(placeholder_surface, (x + 15, y + (field_height - placeholder_surface.get_height()) // 2))

        # Error message
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

    def draw_button(self, screen, text, x, y, width, height, color):
        """Draw a rounded button."""
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, color, button_rect, border_radius=12)

        text_surface = FONT_BUTTON.render(text, True, COLOR_WHITE)
        text_x = x + (width - text_surface.get_width()) // 2
        text_y = y + (height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

    def draw_social_button(self, screen, text, x, y, width, height, provider):
        """Draw a social login button."""
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLOR_WHITE, button_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), button_rect, 1, border_radius=12)

        # Icon
        icon_size = 24
        icon = self.load_social_icon(provider, icon_size)

        text_surface = FONT_BODY.render(text, True, COLOR_BLACK)
        total_width = icon_size + 10 + text_surface.get_width() if icon else text_surface.get_width()
        start_x = x + (width - total_width) // 2

        if icon:
            icon_y = y + (height - icon_size) // 2
            screen.blit(icon, (start_x, icon_y))
            text_x = start_x + icon_size + 10
        else:
            # Fallback circle
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
        """Handle events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            # Back button
            if x < 100 and 45 < y < 85:
                self.reset()
                return "onboarding"

            current_y = 190

            # Email input area
            email_area_end = current_y + 50 + (self.email_error_height + 10 if self.email_error_height > 0 else 0)
            if current_y < y < email_area_end:
                self.active_input = "email"
                self.email_touched = True
                self.global_error = None
                return None
            current_y = email_area_end + 15

            # Password input area
            password_area_end = current_y + 50 + (self.password_error_height + 10 if self.password_error_height > 0 else 0)
            if current_y < y < password_area_end:
                self.active_input = "password"
                self.password_touched = True
                self.global_error = None
                return None

            # Forgot password
            if hasattr(self, 'forgot_password_y') and hasattr(self, 'forgot_password_x'):
                if self.forgot_password_y < y < self.forgot_password_y + 20 and x > self.forgot_password_x:
                    return "forgot_password"

            # Sign In button
            if hasattr(self, 'button_y') and self.button_y < y < self.button_y + 50:
                return self.attempt_login()

            # Apple Sign In
            if hasattr(self, 'apple_button_y') and self.apple_button_y < y < self.apple_button_y + 50:
                if 20 < x < SCREEN_WIDTH - 20:
                    return "apple_signin"

            # Google Sign In
            if hasattr(self, 'google_button_y') and self.google_button_y < y < self.google_button_y + 50:
                if 20 < x < SCREEN_WIDTH - 20:
                    return "google_signin"

            # Sign up link
            if hasattr(self, 'signup_link_y') and self.signup_link_y < y < self.signup_link_y + 30:
                return "signup"

            # Click elsewhere
            if self.active_input == "email":
                self.email_touched = True
            elif self.active_input == "password":
                self.password_touched = True
            self.active_input = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "onboarding"
            elif event.key == pygame.K_RETURN:
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
                self.global_error = None
                if event.key == pygame.K_BACKSPACE:
                    if self.active_input == "email":
                        self.email_text = self.email_text[:-1]
                    else:
                        self.password_text = self.password_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if self.active_input == "email":
                        self.email_text += event.unicode
                    else:
                        self.password_text += event.unicode

        return None