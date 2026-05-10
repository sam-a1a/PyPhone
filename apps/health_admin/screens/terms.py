import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
GREY = (72, 72, 74)

FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)


class AdminTermsScreen:
    def __init__(self):
        self.scroll_y = 0
        self.max_scroll = 400
        self.terms_content = [
            ("1. Medical Staff Agreement", True),
            ("By registering as a medical professional on the Health Admin platform, you agree to maintain the highest standards of patient care and data protection.", False),
            ("", False),
            ("2. Professional Credentials", True),
            ("You certify that all credentials, licenses, and qualifications provided during registration are accurate and current.", False),
            ("", False),
            ("3. Patient Data Protection", True),
            ("You agree to handle all patient information in accordance with HIPAA regulations and local healthcare privacy laws.", False),
            ("", False),
            ("4. System Access", True),
            ("Access to the admin system is granted solely for legitimate healthcare purposes. Unauthorized access or data sharing is strictly prohibited.", False),
            ("", False),
            ("5. Appointment Management", True),
            ("You are responsible for managing your appointments accurately and providing timely care to scheduled patients.", False),
            ("", False),
            ("6. Code of Conduct", True),
            ("All interactions within the platform must maintain professional standards and respect patient dignity.", False),
            ("", False),
            ("7. Data Accuracy", True),
            ("You agree to maintain accurate and up-to-date patient records and medical histories.", False),
            ("", False),
            ("8. Security Responsibilities", True),
            ("You must protect your login credentials and report any suspected security breaches immediately.", False),
            ("", False),
            ("9. Liability", True),
            ("The platform provides tools for healthcare management but does not assume liability for medical decisions.", False),
            ("", False),
            ("10. Terms Updates", True),
            ("We may update these terms periodically. Continued use of the platform constitutes acceptance of updated terms.", False),
        ]

    def reset(self):
        self.scroll_y = 0

    def draw(self, screen):
        screen.fill(COLOR_WHITE)

        pygame.draw.rect(screen, COLOR_WHITE, (0, 40, SCREEN_WIDTH, 60))

        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (15, 55))

        title = FONT_MEDIUM.render("Terms of Service", True, COLOR_BLACK)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(title, (title_x, 55))

        content_area = pygame.Rect(0, 100, SCREEN_WIDTH, SCREEN_HEIGHT - 200)

        y_offset = 110 - self.scroll_y
        for text, is_header in self.terms_content:
            if text:
                if is_header:
                    rendered = FONT_MEDIUM.render(text, True, COLOR_BLACK)
                    if 100 < y_offset < SCREEN_HEIGHT - 120:
                        screen.blit(rendered, (20, y_offset))
                    y_offset += 30
                else:
                    y_offset = self.draw_wrapped_text(screen, text, 20, y_offset, SCREEN_WIDTH - 40)
                    y_offset += 10
            else:
                y_offset += 15

        self.max_scroll = max(0, y_offset + self.scroll_y - SCREEN_HEIGHT + 200)

        if self.max_scroll > 0:
            scroll_bar_height = max(30, (SCREEN_HEIGHT - 200) * (SCREEN_HEIGHT - 200) / (y_offset + self.scroll_y))
            scroll_bar_y = 100 + (self.scroll_y / self.max_scroll) * (SCREEN_HEIGHT - 200 - scroll_bar_height)
            pygame.draw.rect(screen, (200, 200, 200), (SCREEN_WIDTH - 6, scroll_bar_y, 4, scroll_bar_height), border_radius=2)

        button_bg = pygame.Rect(0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100)
        pygame.draw.rect(screen, COLOR_WHITE, button_bg)

        pygame.draw.line(screen, (230, 230, 230), (0, SCREEN_HEIGHT - 100), (SCREEN_WIDTH, SCREEN_HEIGHT - 100), 1)

        self.draw_button(screen, "Accept & Continue", 20, SCREEN_HEIGHT - 80, SCREEN_WIDTH - 40, 50, BLUE)

    def draw_wrapped_text(self, screen, text, x, y, max_width):
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
            if 100 < y < SCREEN_HEIGHT - 120:
                text_surface = FONT_SMALL.render(line, True, GREY)
                screen.blit(text_surface, (x, y))
            y += FONT_SMALL.get_height() + 4

        return y

    def draw_button(self, screen, text, x, y, width, height, color):
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, color, button_rect, border_radius=12)

        text_surface = FONT_BUTTON.render(text, True, COLOR_WHITE)
        text_x = x + (width - text_surface.get_width()) // 2
        text_y = y + (height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if x < 100 and 45 < y < 85:
                self.reset()
                return "signup"

            if SCREEN_HEIGHT - 80 < y < SCREEN_HEIGHT - 30:
                self.reset()
                return "signup_accepted"

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.reset()
                return "signup"
            elif event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))

        return None