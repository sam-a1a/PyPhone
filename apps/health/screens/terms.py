import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.health.components import draw_button

BLUE = (0, 122, 255)
GREY = (72, 72, 74)

FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)


class TermsScreen:

    def __init__(self):
        self.scroll_y = 0
        self.terms_content = [
            ("1. Acceptance of Terms", True),
            ("By accessing and using the Health app, you agree to be bound by these Terms of Service.", False),
            ("", False),
            ("2. Health Data", True),
            ("The Health app collects personal health information including steps, heart rate, and sleep patterns.",
             False),
            ("", False),
            ("3. Privacy", True),
            ("Your privacy is important to us. Your health data is encrypted and stored securely.", False),
            ("", False),
            ("4. Medical Disclaimer", True),
            ("The Health app is not a medical device and is not intended to diagnose or treat any disease.", False),
            ("", False),
            ("5. User Responsibilities", True),
            ("You are responsible for maintaining the confidentiality of your account credentials.", False),
            ("", False),
            ("6. Limitation of Liability", True),
            ("The Health app is provided 'as is' without warranties of any kind.", False),
            ("", False),
            ("7. Changes to Terms", True),
            ("We reserve the right to modify these terms at any time.", False),
        ]

    def draw(self, screen):
        screen.fill(COLOR_WHITE)

        pygame.draw.rect(screen, COLOR_WHITE, (0, 40, SCREEN_WIDTH, 60))

        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        title = FONT_MEDIUM.render("Terms of Service", True, COLOR_BLACK)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(title, (title_x, 55))

        y_offset = 110 - self.scroll_y
        for text, is_header in self.terms_content:
            if text:
                if is_header:
                    rendered = FONT_MEDIUM.render(text, True, COLOR_BLACK)
                    screen.blit(rendered, (20, y_offset))
                    y_offset += 30
                else:
                    y_offset = self.draw_wrapped_text(screen, text, 20, y_offset, SCREEN_WIDTH - 40)
                    y_offset += 10
            else:
                y_offset += 15

        pygame.draw.rect(screen, COLOR_WHITE, (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        draw_button(screen, "Accept & Continue", 20, SCREEN_HEIGHT - 80, SCREEN_WIDTH - 40, 50, BLUE)

    def draw_wrapped_text(self, screen, text, x, y, max_width):
        """Draw wrapped text."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = FONT_SMALL.render(test_line, True, GREY)
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        for line in lines:
            text_surface = FONT_SMALL.render(line, True, GREY)
            screen.blit(text_surface, (x, y))
            y += FONT_SMALL.get_height() + 4

        return y

    def handle_event(self, event):
        """Handle events. Returns next screen name or None."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if 15 < x < 80 and 50 < y < 80:
                return "signup"

            if SCREEN_HEIGHT - 80 < y < SCREEN_HEIGHT - 30:
                return "signup_accepted"

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "signup"

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 20
            self.scroll_y = max(0, self.scroll_y)

        return None