import pygame
from config import COLOR_WHITE, COLOR_BLACK

FONT_CARD_TITLE = pygame.font.SysFont("Arial", 13)
FONT_CARD_VALUE = pygame.font.SysFont("Arial", 32, bold=True)
FONT_CARD_LABEL = pygame.font.SysFont("Arial", 11)
FONT_SECTION = pygame.font.SysFont("Arial", 16, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 13)


def draw_stat_card(screen, x, y, width, height, title, value, color, icon=None):

    card_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

    accent_rect = pygame.Rect(x, y, 5, height)
    pygame.draw.rect(screen, color, accent_rect,
                     border_top_left_radius=15, border_bottom_left_radius=15)

    if icon:
        icon_font = pygame.font.SysFont("Segoe UI Emoji", 20)
        icon_surface = icon_font.render(icon, True, color)
        screen.blit(icon_surface, (x + 15, y + 12))

    title_surface = FONT_CARD_TITLE.render(title, True, (100, 100, 100))
    screen.blit(title_surface, (x + 15, y + 40))

    value_surface = FONT_CARD_VALUE.render(str(value), True, color)
    screen.blit(value_surface, (x + 15, y + 58))


def draw_info_card(screen, x, y, width, height, title, items):
    card_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

    title_surface = FONT_SECTION.render(title, True, COLOR_BLACK)
    screen.blit(title_surface, (x + 20, y + 15))

    item_y = y + 50
    line_height = 28

    for item in items:
        if len(item) > 50:
            item = item[:47] + "..."

        item_surface = FONT_BODY.render(item, True, (80, 80, 80))
        screen.blit(item_surface, (x + 20, item_y))
        item_y += line_height


def draw_detail_row(screen, x, y, width, label, value):
    row_height = 30

    label_surface = FONT_BODY.render(f"{label}:", True, (100, 100, 100))
    screen.blit(label_surface, (x, y))

    value_str = str(value) if value else "N/A"
    if len(value_str) > 40:
        value_str = value_str[:37] + "..."

    value_surface = FONT_BODY.render(value_str, True, COLOR_BLACK)
    screen.blit(value_surface, (x + 120, y))

    return row_height