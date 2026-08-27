#iOS-style notification banner
"""
The banner that slides down from under the Dynamic Island: app icon, app name,
"now", a title and a body line. Slides in with an ease-out, holds, then slides
back up. Tapping it dismisses it early.

Drawn last, over everything including the bezel, the way a real notification
sits above whatever app is open.
"""
import pygame

from config import SCREEN_WIDTH
from components.icons import load_icon_image, create_fallback_icon

BANNER_MARGIN = 10
BANNER_HEIGHT = 78
BANNER_RADIUS = 22
BANNER_RESTING_Y = 52          # clear of the status bar and the island
ICON_SIZE = 38

SLIDE_IN_SECONDS = 0.42
SLIDE_OUT_SECONDS = 0.28
DEFAULT_HOLD_SECONDS = 4.5

BANNER_BG = (250, 250, 252)
BANNER_BORDER = (225, 225, 230)
SHADOW = (0, 0, 0, 45)
TITLE_COLOR = (0, 0, 0)
BODY_COLOR = (60, 60, 67)
META_COLOR = (140, 140, 148)

FONT_APP = pygame.font.SysFont("Arial", 12)
FONT_TITLE = pygame.font.SysFont("Arial", 15, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 14)


def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def _ease_in_cubic(t):
    return t ** 3


class NotificationBanner:
    """One banner at a time; a new show() replaces whatever is on screen."""

    def __init__(self):
        self.visible = False
        self.app_name = ""
        self.title = ""
        self.body = ""
        self.icon = None
        self._phase = "hidden"      # hidden | sliding_in | holding | sliding_out
        self._elapsed = 0.0
        self._hold_seconds = DEFAULT_HOLD_SECONDS
        self._clock = pygame.time.Clock()

    def show(self, app_name, title, body, icon_name=None,
             hold_seconds=DEFAULT_HOLD_SECONDS):
        self.app_name = app_name.upper()
        self.title = title
        self.body = body
        self.icon = self._load_icon(icon_name)
        self._hold_seconds = hold_seconds
        self._phase = "sliding_in"
        self._elapsed = 0.0
        self.visible = True

    @staticmethod
    def _load_icon(icon_name):
        if not icon_name:
            return None
        size = (ICON_SIZE, ICON_SIZE)
        icon = load_icon_image(icon_name, size)
        if icon is None:
            icon = create_fallback_icon((0, 122, 255), size)
        return icon

    def dismiss(self):
        #Slide away early, e.g. the user tapped it
        if self._phase in ("sliding_in", "holding"):
            self._phase = "sliding_out"
            self._elapsed = 0.0

    def hide(self):
        #Disappear immediately, no animation
        self.visible = False
        self._phase = "hidden"
        self._elapsed = 0.0

    def update(self, dt=None):
        #Advance the animation. dt in seconds; measured from the clock if omitted
        if not self.visible:
            return

        if dt is None:
            dt = self._clock.tick(60) / 1000.0
        self._elapsed += dt

        if self._phase == "sliding_in" and self._elapsed >= SLIDE_IN_SECONDS:
            self._phase = "holding"
            self._elapsed = 0.0
        elif self._phase == "holding" and self._elapsed >= self._hold_seconds:
            self._phase = "sliding_out"
            self._elapsed = 0.0
        elif self._phase == "sliding_out" and self._elapsed >= SLIDE_OUT_SECONDS:
            self.hide()

    def _offscreen_y(self):
        return -(BANNER_HEIGHT + 20)

    def current_y(self):
        #Where the top of the banner sits this frame
        if not self.visible:
            return self._offscreen_y()

        start = self._offscreen_y()
        if self._phase == "sliding_in":
            progress = _ease_out_cubic(min(1.0, self._elapsed / SLIDE_IN_SECONDS))
            return start + (BANNER_RESTING_Y - start) * progress
        if self._phase == "sliding_out":
            progress = _ease_in_cubic(min(1.0, self._elapsed / SLIDE_OUT_SECONDS))
            return BANNER_RESTING_Y + (start - BANNER_RESTING_Y) * progress
        return BANNER_RESTING_Y

    def get_rect(self):
        width = SCREEN_WIDTH - BANNER_MARGIN * 2
        return pygame.Rect(BANNER_MARGIN, int(self.current_y()), width, BANNER_HEIGHT)

    def handle_event(self, event):
        #True if the banner swallowed the event, so the screen behind ignores it
        if not self.visible or self._phase == "sliding_out":
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and self.get_rect().collidepoint(event.pos):
            self.dismiss()
            return True
        return False

    def draw(self, screen):
        if not self.visible:
            return

        rect = self.get_rect()

        # Soft shadow, offset down a few pixels
        shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, SHADOW, shadow.get_rect(), border_radius=BANNER_RADIUS)
        screen.blit(shadow, (rect.x, rect.y + 4))

        pygame.draw.rect(screen, BANNER_BG, rect, border_radius=BANNER_RADIUS)
        pygame.draw.rect(screen, BANNER_BORDER, rect, 1, border_radius=BANNER_RADIUS)

        icon_x = rect.x + 14
        icon_y = rect.y + 12
        if self.icon is not None:
            screen.blit(self.icon, (icon_x, icon_y))

        text_x = icon_x + ICON_SIZE + 12
        text_right = rect.right - 14

        app_label = FONT_APP.render(self.app_name, True, META_COLOR)
        screen.blit(app_label, (text_x, rect.y + 13))

        now_label = FONT_APP.render("now", True, META_COLOR)
        screen.blit(now_label, (text_right - now_label.get_width(), rect.y + 13))

        title = FONT_TITLE.render(self.title, True, TITLE_COLOR)
        screen.blit(title, (text_x, rect.y + 30))

        body = self._truncate(self.body, FONT_BODY, text_right - text_x)
        body_surface = FONT_BODY.render(body, True, BODY_COLOR)
        screen.blit(body_surface, (text_x, rect.y + 50))

    @staticmethod
    def _truncate(text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis
