import pygame
import re
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
GREEN = (52, 199, 89)
RED = (255, 59, 48)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class AdminForgotPasswordScreen:

    def __init__(self):
        self.email_text = ""
        self.active_input = None
        self.email_touched = False

        # Error animation
        self.email_error_height = 0
        self.max_error_height = 18
        self.animation_speed = 2

        # Success state
        self.email_sent = False
        self.success_message_alpha = 0

        # Key repeat
        pygame.key.set_repeat(400, 50)

    def reset(self):
        """Reset screen state."""
        self.email_text = ""
        self.active_input = None
        self.email_touched = False
        self.email_error_height = 0
        self.email_sent = False
        self.success_message_alpha = 0

    def validate_email(self):
        """Validate email field."""
        if not self.email_touched:
            return None
        if not self.email_text:
            return "Email is required"
        if not EMAIL_PATTERN.match(self.email_text):
            return "Please enter a valid email address"
        return None

    def is_email_valid(self):
        """Check if email is valid."""
        return EMAIL_PATTERN.match(self.email_text) is not None

    def update_animations(self):
        """Update animations."""
        # Email error animation
        email_error = self.validate_email()
        if email_error:
            self.email_error_height = min(self.email_error_height + self.animation_speed, self.max_error_height)
        else:
            self.email_error_height = max(self.email_error_height - self.animation_speed, 0)

        # Success message fade in
        if self.email_sent:
            self.success_message_alpha = min(self.success_message_alpha + 10, 255)

    def draw(self, screen):
        """Draw the forgot password screen."""
        self.update_animations()

        screen.fill(COLOR_WHITE)

        # Back button
        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        if not self.email_sent:
            self.draw_request_form(screen)
        else:
            self.draw_success_message(screen)

    def draw_request_form(self, screen):
        """Draw the password reset request form."""
        # Title
        title = FONT_TITLE.render("Reset Password", True, COLOR_BLACK)
        screen.blit(title, (20, 100))

        # Description
        desc_lines = [
            "Enter the email address associated",
            "with your doctor account and we'll",
            "send you a link to reset your password."
        ]
        y = 150
        for line in desc_lines:
            desc_text = FONT_BODY.render(line, True, GREY)
            screen.blit(desc_text, (20, y))
            y += 24

        # Email input
        current_y = 250
        email_error = self.validate_email()
        current_y = self.draw_input_field(
            screen, "Email Address", self.email_text,
            20, current_y, SCREEN_WIDTH - 40,
            self.active_input == "email",
            email_error, self.email_error_height
        )
        current_y += 30

        # Send Reset Link button
        self.button_y = current_y
        button_color = BLUE if self.is_email_valid() else GREY
        self.draw_button(screen, "Send Reset Link", 20, current_y, SCREEN_WIDTH - 40, 50, button_color)

    def draw_success_message(self, screen):
        """Draw the success message after email is sent."""
        center_x = SCREEN_WIDTH // 2
        center_y = 200

        # Checkmark circle with fade in
        circle_surface = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (*GREEN, self.success_message_alpha), (60, 60), 60)
        screen.blit(circle_surface, (center_x - 60, center_y - 60))

        # Checkmark
        if self.success_message_alpha > 100:
            check_alpha = min(255, (self.success_message_alpha - 100) * 3)
            check_surface = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.line(check_surface, (255, 255, 255, check_alpha),
                           (35, 60), (55, 80), 5)
            pygame.draw.line(check_surface, (255, 255, 255, check_alpha),
                           (55, 80), (85, 40), 5)
            screen.blit(check_surface, (center_x - 60, center_y - 60))

        # Title
        title = FONT_TITLE.render("Check Your Email", True, COLOR_BLACK)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(title, (title_x, 300))

        # Description
        desc_lines = [
            "We've sent a password reset link to:",
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

        # Didn't receive email
        y += 30
        didnt_receive = FONT_SMALL.render("Didn't receive the email?", True, GREY)
        screen.blit(didnt_receive, (center_x - didnt_receive.get_width() // 2, y))

        y += 25
        self.resend_y = y
        resend_link = FONT_SMALL.render("Resend", True, BLUE)
        screen.blit(resend_link, (center_x - resend_link.get_width() // 2, y))

        # Back to Sign In button
        self.back_button_y = 600
        self.draw_button(screen, "Back to Sign In", 20, self.back_button_y, SCREEN_WIDTH - 40, 50, BLUE)

    def draw_input_field(self, screen, placeholder, value, x, y, width, is_active, error=None, error_height=0):
        """Draw an input field."""
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

    def handle_event(self, event):
        """Handle events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            # Back button (top left)
            if x < 100 and 45 < y < 85:
                self.reset()
                return "login"

            if not self.email_sent:
                # Email input area
                if 250 < y < 320:
                    self.active_input = "email"
                    self.email_touched = True
                    return None

                # Send Reset Link button
                if hasattr(self, 'button_y') and self.button_y < y < self.button_y + 50:
                    if self.is_email_valid():
                        self.email_sent = True
                    else:
                        self.email_touched = True
                    return None

                # Click elsewhere
                if self.active_input == "email":
                    self.email_touched = True
                self.active_input = None

            else:
                # Success screen

                # Resend link
                if hasattr(self, 'resend_y') and self.resend_y < y < self.resend_y + 25:
                    self.success_message_alpha = 0
                    return None

                # Back to Sign In button
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