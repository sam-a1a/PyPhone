#Verification code entry
"""
The screen between filling in a signup form and the account existing. Six
boxes, one per digit, filled as you type. The code itself arrives as a system
notification banner, so the user reads it off the top of the screen and types
it back in here.

Shared by both apps; the accent colour and app name are passed in so it looks
native to whichever one launched it.
"""
import pygame

from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK
from apps.shared import verification as verification_module
from apps.shared.verification import CODE_LENGTH, OK, MESSAGES

GREY = (142, 142, 147)
LIGHT_GREY = (242, 242, 247)
RED = (255, 59, 48)
BOX_BORDER = (210, 210, 215)

FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_CODE = pygame.font.SysFont("Arial", 30, bold=True)

BOX_WIDTH = 48
BOX_HEIGHT = 58
BOX_GAP = 10
BOXES_Y = 300


class VerifyScreen:

    def __init__(self, app_name="Health", accent=(0, 122, 255),
                 service=None, back_target="signup"):
        self.app_name = app_name
        self.accent = accent
        # Defaults to the shared service, overridable for tests
        self.service = service or verification_module.verification
        self.back_target = back_target

        self.email = ""
        self.digits = ""
        self.error = None
        self.resend_notice = None
        self._resend_requested = False

        pygame.key.set_repeat(400, 50)

    def start(self, email):
        #Called when the signup form has been submitted and a code just went out
        self.email = email
        self.digits = ""
        self.error = None
        self.resend_notice = None
        self._resend_requested = False

    def take_resend_request(self) -> bool:
        #True once after the user asks for a new code, so the app can re-notify
        requested = self._resend_requested
        self._resend_requested = False
        return requested

    @property
    def is_complete(self) -> bool:
        return len(self.digits) == CODE_LENGTH

    def submit(self):
        #Check the typed code. Returns "verified" on success, else None
        if not self.is_complete:
            self.error = f"Enter all {CODE_LENGTH} digits"
            return None

        outcome = self.service.verify(self.email, self.digits)
        if outcome == OK:
            self.error = None
            return "verified"

        self.error = MESSAGES.get(outcome, "That code is not right")
        self.digits = ""
        return None

    def request_resend(self):
        if not self.service.can_resend(self.email):
            wait = self.service.seconds_until_resend(self.email)
            self.resend_notice = f"Wait {wait}s before requesting another code"
            return
        self.service.send_code(self.email)
        self._resend_requested = True
        self.digits = ""
        self.error = None
        self.resend_notice = "A new code is on its way"

    # Drawing

    def draw(self, screen):
        screen.fill(COLOR_WHITE)

        back = FONT_BODY.render("< Back", True, self.accent)
        screen.blit(back, (15, 55))
        self.back_rect = pygame.Rect(10, 50, 90, 30)

        title = FONT_TITLE.render("Verify your email", True, COLOR_BLACK)
        screen.blit(title, (20, 110))

        subtitle = FONT_BODY.render(f"We sent a {CODE_LENGTH}-digit code to", True, GREY)
        screen.blit(subtitle, (20, 155))

        email_label = FONT_BODY.render(self.email or "your email", True, COLOR_BLACK)
        screen.blit(email_label, (20, 180))

        hint = FONT_SMALL.render("It arrives as a notification at the top of the screen.",
                                 True, GREY)
        screen.blit(hint, (20, 215))

        self._draw_boxes(screen)

        y = BOXES_Y + BOX_HEIGHT + 20
        if self.error:
            error_text = FONT_SMALL.render(self.error, True, RED)
            screen.blit(error_text, (20, y))
            y += 24
        elif self.resend_notice:
            notice = FONT_SMALL.render(self.resend_notice, True, GREY)
            screen.blit(notice, (20, y))
            y += 24

        self.button_y = max(y + 20, BOXES_Y + BOX_HEIGHT + 60)
        self._draw_verify_button(screen, self.button_y)

        self.resend_y = self.button_y + 70
        resend = FONT_BODY.render("Resend code", True, self.accent)
        self.resend_rect = pygame.Rect(
            (SCREEN_WIDTH - resend.get_width()) // 2, self.resend_y,
            resend.get_width(), 24
        )
        screen.blit(resend, self.resend_rect.topleft)

    def _draw_boxes(self, screen):
        total = CODE_LENGTH * BOX_WIDTH + (CODE_LENGTH - 1) * BOX_GAP
        start_x = (SCREEN_WIDTH - total) // 2
        active_index = min(len(self.digits), CODE_LENGTH - 1)

        for i in range(CODE_LENGTH):
            x = start_x + i * (BOX_WIDTH + BOX_GAP)
            rect = pygame.Rect(x, BOXES_Y, BOX_WIDTH, BOX_HEIGHT)

            filled = i < len(self.digits)
            is_active = i == active_index and not self.is_complete

            pygame.draw.rect(screen, LIGHT_GREY if not filled else COLOR_WHITE,
                             rect, border_radius=12)
            border = RED if self.error else (self.accent if is_active else BOX_BORDER)
            pygame.draw.rect(screen, border, rect, 2 if is_active or self.error else 1,
                             border_radius=12)

            if filled:
                digit = FONT_CODE.render(self.digits[i], True, COLOR_BLACK)
                screen.blit(digit, (rect.centerx - digit.get_width() // 2,
                                    rect.centery - digit.get_height() // 2))

    def _draw_verify_button(self, screen, y):
        enabled = self.is_complete
        rect = pygame.Rect(20, y, SCREEN_WIDTH - 40, 50)
        pygame.draw.rect(screen, self.accent if enabled else (200, 200, 205),
                         rect, border_radius=12)
        label = FONT_BODY.render("Verify", True, COLOR_WHITE)
        screen.blit(label, (rect.centerx - label.get_width() // 2,
                            rect.centery - label.get_height() // 2))

    # Events

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if hasattr(self, 'back_rect') and self.back_rect.collidepoint(x, y):
                return self.back_target

            if hasattr(self, 'resend_rect') and self.resend_rect.collidepoint(x, y):
                self.request_resend()
                return None

            if hasattr(self, 'button_y') and self.button_y < y < self.button_y + 50:
                if 20 < x < SCREEN_WIDTH - 20:
                    return self.submit()
                return None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return self.back_target

            if event.key == pygame.K_RETURN:
                return self.submit()

            if event.key == pygame.K_BACKSPACE:
                self.digits = self.digits[:-1]
                self.error = None
                return None

            if event.unicode and event.unicode.isdigit():
                if len(self.digits) < CODE_LENGTH:
                    self.digits += event.unicode
                    self.error = None
                    # Filling the last box submits, the way iOS does
                    if self.is_complete:
                        return self.submit()

        return None
