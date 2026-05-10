import os

import pygame

from config import COLOR_WHITE, COLOR_BLACK

FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")

_social_icon_cache = {}


def load_social_icon(provider, size=24):
    cache_key = f"{provider}_{size}"

    if cache_key in _social_icon_cache:
        return _social_icon_cache[cache_key]

    icon_path = os.path.join(ICON_DIR, f"{provider}.png")

    if os.path.exists(icon_path):
        try:
            icon = pygame.image.load(icon_path).convert_alpha()
            icon = pygame.transform.smoothscale(icon, (size, size))
            _social_icon_cache[cache_key] = icon
            return icon
        except (pygame.error, OSError):
            pass

    return None


def draw_button(screen, text, x, y, width, height, color):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, color, button_rect, border_radius=12)

    text_surface = FONT_BUTTON.render(text, True, COLOR_WHITE)
    text_x = x + (width - text_surface.get_width()) // 2
    text_y = y + (height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))


def draw_text_button(screen, text, x, y, color):
    text_surface = FONT_BODY.render(text, True, color)
    text_x = x - text_surface.get_width() // 2
    screen.blit(text_surface, (text_x, y))


def draw_social_button(screen, text, x, y, width, height, provider):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, COLOR_WHITE, button_rect, border_radius=12)
    pygame.draw.rect(screen, (220, 220, 220), button_rect, 1, border_radius=12)

    icon_size = 24
    icon = load_social_icon(provider, icon_size)

    text_surface = FONT_BODY.render(text, True, COLOR_BLACK)
    total_width = icon_size + 10 + text_surface.get_width() if icon else text_surface.get_width()
    start_x = x + (width - total_width) // 2

    if icon:
        icon_y = y + (height - icon_size) // 2
        screen.blit(icon, (start_x, icon_y))
        text_x = start_x + icon_size + 10
    else:
        icon_x = start_x + icon_size // 2
        icon_y = y + height // 2
        if provider == "apple":
            pygame.draw.circle(screen, COLOR_BLACK, (icon_x, icon_y), 12)
        elif provider == "google":
            pygame.draw.circle(screen, (234, 67, 53), (icon_x, icon_y), 12)
        text_x = start_x + icon_size + 10

    text_y = y + (height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))