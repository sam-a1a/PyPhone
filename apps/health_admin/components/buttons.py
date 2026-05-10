import pygame
from config import COLOR_WHITE, COLOR_BLACK

FONT_BUTTON = pygame.font.SysFont("Arial", 14, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 13)

BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
GREY = (142, 142, 147)


def draw_button(screen, text, x, y, width, height, color, text_color=COLOR_WHITE):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, color, button_rect, border_radius=10)

    text_surface = FONT_BUTTON.render(text, True, text_color)
    text_x = x + (width - text_surface.get_width()) // 2
    text_y = y + (height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))

    return button_rect


def draw_text_button(screen, text, x, y, color):

    text_surface = FONT_BODY.render(text, True, color)
    screen.blit(text_surface, (x, y))

    return pygame.Rect(x, y, text_surface.get_width(), text_surface.get_height())


def draw_icon_button(screen, icon_text, x, y, size, color, bg_color=None):

    button_rect = pygame.Rect(x, y, size, size)

    if bg_color:
        pygame.draw.rect(screen, bg_color, button_rect, border_radius=8)

    icon_font = pygame.font.SysFont("Segoe UI Emoji", size // 2)
    icon_surface = icon_font.render(icon_text, True, color)
    icon_x = x + (size - icon_surface.get_width()) // 2
    icon_y = y + (size - icon_surface.get_height()) // 2
    screen.blit(icon_surface, (icon_x, icon_y))

    return button_rect


def draw_back_button(screen, x, y):

    button_rect = pygame.Rect(x, y, 80, 36)
    pygame.draw.rect(screen, (220, 220, 220), button_rect, border_radius=8)

    text_surface = FONT_BUTTON.render("← Back", True, COLOR_BLACK)
    text_x = x + (80 - text_surface.get_width()) // 2
    text_y = y + (36 - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))

    return button_rect


def draw_add_button(screen, x, y, text="+ Add New"):

    width = 100
    height = 36
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, BLUE, button_rect, border_radius=8)

    text_surface = FONT_BUTTON.render(text, True, COLOR_WHITE)
    text_x = x + (width - text_surface.get_width()) // 2
    text_y = y + (height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))

    return button_rect