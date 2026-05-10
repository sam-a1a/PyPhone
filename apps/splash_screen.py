import pygame
import os
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CORNER_RADIUS,
    COLOR_BLACK
)
from components import draw_status_bar

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")

def load_app_icon(app_name, size=120):
    icon_name = app_name.lower().replace(" ", "")
    icon_path = os.path.join(ICON_DIR, f"{icon_name}.png")

    if os.path.exists(icon_path):
        try:
            icon = pygame.image.load(icon_path).convert_alpha()
            return pygame.transform.smoothscale(icon, (size, size))
        except (pygame.error, OSError):
            pass
    return None


def create_fallback_icon(color, size=120):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, size, size), border_radius=int(size * 0.22))
    return surface


def show_splash_screen(screen, app_color, app_name):
    clock = pygame.time.Clock()
    fps = 60

    icon_size = 120
    icon_image = load_app_icon(app_name, icon_size)
    if icon_image is None:
        icon_image = create_fallback_icon(app_color, icon_size)

    icon_x = (SCREEN_WIDTH - icon_size) // 2
    icon_y = (SCREEN_HEIGHT - icon_size) // 2

    hold_duration = 0.5
    hold_frames = int(hold_duration * fps)

    for frame in range(hold_frames):
        screen.fill(app_color)
        screen.blit(icon_image, (icon_x, icon_y))

        draw_status_bar(screen, dark_mode=False)
        pygame.draw.rect(
            screen, COLOR_BLACK,
            (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            10, border_radius=CORNER_RADIUS
        )

        pygame.display.flip()
        clock.tick(fps)

    fade_duration = 0.3
    fade_frames = int(fade_duration * fps)

    splash_screen = screen.copy()

    for frame in range(fade_frames):
        progress = frame / fade_frames
        alpha = int(255 * (1 - progress))

        screen.fill(app_color)

        splash_screen.set_alpha(alpha)
        screen.blit(splash_screen, (0, 0))

        draw_status_bar(screen, dark_mode=False)
        pygame.draw.rect(
            screen, COLOR_BLACK,
            (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            10, border_radius=CORNER_RADIUS
        )

        pygame.display.flip()
        clock.tick(fps)