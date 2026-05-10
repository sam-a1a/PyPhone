import pygame
from config import COLOR_WHITE, COLOR_BLACK

FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_ERROR = pygame.font.SysFont("Arial", 12)

BLUE = (0, 122, 255)
GREY = (180, 180, 180)
RED = (255, 59, 48)
GREEN = (52, 199, 89)

def draw_input_field(screen, placeholder, value, x, y, width, is_active, error=None, error_height=0):
    field_height = 50

    if error and error_height > 0:
        border_color = RED
    elif is_active:
        border_color = BLUE
    else:
        border_color = (220, 220, 220)

    input_rect = pygame.Rect(x, y, width, field_height)
    pygame.draw.rect(screen, COLOR_WHITE, input_rect, border_radius=10)
    pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)

    if value:
        text_surface = FONT_BODY.render(value, True, COLOR_BLACK)
        screen.blit(text_surface, (x + 15, y + (field_height - text_surface.get_height()) // 2))

        if is_active:
            cursor_x = x + 15 + text_surface.get_width() + 2
            cursor_y_start = y + 12
            cursor_y_end = y + field_height - 12
            pygame.draw.line(screen, COLOR_BLACK, (cursor_x, cursor_y_start), (cursor_x, cursor_y_end), 2)
    else:
        if is_active:
            cursor_x = x + 15
            cursor_y_start = y + 12
            cursor_y_end = y + field_height - 12
            pygame.draw.line(screen, COLOR_BLACK, (cursor_x, cursor_y_start), (cursor_x, cursor_y_end), 2)
        else:
            placeholder_surface = FONT_BODY.render(placeholder, True, GREY)
            screen.blit(placeholder_surface, (x + 15, y + (field_height - placeholder_surface.get_height()) // 2))

    if error and error_height > 0:
        error_surface = FONT_ERROR.render(error, True, RED)
        error_y = y + field_height + 5

        if error_height >= error_surface.get_height():
            screen.blit(error_surface, (x + 5, error_y))
        else:
            clip_rect = pygame.Rect(0, 0, error_surface.get_width(), int(error_height))
            screen.blit(error_surface, (x + 5, error_y), clip_rect)

    return field_height + error_height + (10 if error_height > 0 else 0)

def draw_checkbox(screen, x, y, checked):
    box_rect = pygame.Rect(x, y, 24, 24)
    if checked:
        pygame.draw.rect(screen, BLUE, box_rect, border_radius=6)
        pygame.draw.line(screen, COLOR_WHITE, (x + 6, y + 12), (x + 10, y + 17), 2)
        pygame.draw.line(screen, COLOR_WHITE, (x + 10, y + 17), (x + 18, y + 7), 2)
    else:
        pygame.draw.rect(screen, COLOR_WHITE, box_rect, border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), box_rect, 2, border_radius=6)