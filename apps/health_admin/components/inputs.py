import pygame
from config import COLOR_WHITE, COLOR_BLACK

FONT_LABEL = pygame.font.SysFont("Arial", 12, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 14)
FONT_ERROR = pygame.font.SysFont("Arial", 11)

BLUE = (0, 122, 255)
GREY = (180, 180, 180)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
BORDER_COLOR = (220, 220, 220)


def draw_input_field(screen, label, placeholder, value, x, y, width, is_active,
                     is_password=False, error=None, error_height=0):

    field_height = 50
    total_y = y

    if label:
        label_surface = FONT_LABEL.render(label, True, (80, 80, 80))
        screen.blit(label_surface, (x, total_y))
        total_y += 20

    if error and error_height > 0:
        border_color = RED
    elif is_active:
        border_color = BLUE
    else:
        border_color = BORDER_COLOR

    input_rect = pygame.Rect(x, total_y, width, field_height)
    pygame.draw.rect(screen, COLOR_WHITE, input_rect, border_radius=10)
    pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)

    display_value = "•" * len(value) if is_password and value else value

    if display_value:
        text_surface = FONT_BODY.render(display_value, True, COLOR_BLACK)

        max_width = width - 30
        clipped = display_value
        while text_surface.get_width() > max_width and len(clipped) > 0:
            clipped = clipped[1:]
            if is_password:
                text_surface = FONT_BODY.render("•" * len(clipped), True, COLOR_BLACK)
            else:
                text_surface = FONT_BODY.render(clipped, True, COLOR_BLACK)

        screen.blit(text_surface, (x + 15, total_y + (field_height - text_surface.get_height()) // 2))

        if is_active:
            cursor_x = x + 15 + text_surface.get_width() + 2
            cursor_y_start = total_y + 12
            cursor_y_end = total_y + field_height - 12
            pygame.draw.line(screen, COLOR_BLACK, (cursor_x, cursor_y_start), (cursor_x, cursor_y_end), 2)
    else:
        if is_active:
            cursor_x = x + 15
            pygame.draw.line(screen, COLOR_BLACK, (cursor_x, total_y + 12), (cursor_x, total_y + field_height - 12), 2)
        else:
            placeholder_surface = FONT_BODY.render(placeholder, True, GREY)
            screen.blit(placeholder_surface, (x + 15, total_y + (field_height - placeholder_surface.get_height()) // 2))

    if error and error_height > 0:
        error_surface = FONT_ERROR.render(error, True, RED)
        error_y = total_y + field_height + 5

        if error_height >= error_surface.get_height():
            screen.blit(error_surface, (x + 5, error_y))
        else:
            clip_rect = pygame.Rect(0, 0, error_surface.get_width(), int(error_height))
            screen.blit(error_surface, (x + 5, error_y), clip_rect)

    return input_rect


def draw_checkbox(screen, x, y, checked, label=None):
    box_size = 24
    box_rect = pygame.Rect(x, y, box_size, box_size)

    if checked:
        pygame.draw.rect(screen, BLUE, box_rect, border_radius=6)
        pygame.draw.line(screen, COLOR_WHITE, (x + 6, y + 12), (x + 10, y + 17), 2)
        pygame.draw.line(screen, COLOR_WHITE, (x + 10, y + 17), (x + 18, y + 7), 2)
    else:
        pygame.draw.rect(screen, COLOR_WHITE, box_rect, border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), box_rect, 2, border_radius=6)

    if label:
        label_surface = FONT_BODY.render(label, True, COLOR_BLACK)
        screen.blit(label_surface, (x + box_size + 8, y + (box_size - label_surface.get_height()) // 2))
        box_rect.width += 8 + label_surface.get_width()

    return box_rect


def draw_dropdown(screen, label, value, options, x, y, width, is_open=False, error=None):
    field_height = 45
    label_height = 20

    label_surface = FONT_LABEL.render(label, True, (80, 80, 80))
    screen.blit(label_surface, (x, y))

    input_y = y + label_height
    input_rect = pygame.Rect(x, input_y, width, field_height)

    if error:
        border_color = RED
    elif is_open:
        border_color = BLUE
    else:
        border_color = BORDER_COLOR

    pygame.draw.rect(screen, COLOR_WHITE, input_rect, border_radius=10)
    pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)

    if value:
        display_text = value
        if len(display_text) > 25:
            display_text = display_text[:22] + "..."
        text_surface = FONT_BODY.render(display_text, True, COLOR_BLACK)
    else:
        text_surface = FONT_BODY.render(f"Select {label.lower()}", True, GREY)

    screen.blit(text_surface, (x + 12, input_y + (field_height - text_surface.get_height()) // 2))

    arrow = "▼" if not is_open else "▲"
    arrow_surface = FONT_BODY.render(arrow, True, GREY)
    screen.blit(arrow_surface, (x + width - 25, input_y + (field_height - arrow_surface.get_height()) // 2))

    option_rects = []

    if is_open and options:
        max_visible = 4
        option_height = 36
        visible_options = options[:max_visible]
        dropdown_height = len(visible_options) * option_height

        dropdown_y = input_y + field_height + 2
        dropdown_rect = pygame.Rect(x, dropdown_y, width, dropdown_height)

        pygame.draw.rect(screen, (200, 200, 200), pygame.Rect(x + 2, dropdown_y + 2, width, dropdown_height), border_radius=8)
        pygame.draw.rect(screen, COLOR_WHITE, dropdown_rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, dropdown_rect, 1, border_radius=8)

        for i, option in enumerate(visible_options):
            option_y = dropdown_y + (i * option_height)
            option_rect = pygame.Rect(x, option_y, width, option_height)
            option_rects.append({"rect": option_rect, "value": option})

            if option == value:
                highlight = pygame.Surface((width - 4, option_height - 4), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (0, 122, 255, 30), (0, 0, width - 4, option_height - 4), border_radius=6)
                screen.blit(highlight, (x + 2, option_y + 2))

            option_text = option[:30] + "..." if len(option) > 30 else option
            option_surface = FONT_BODY.render(option_text, True, COLOR_BLACK)
            screen.blit(option_surface, (x + 12, option_y + (option_height - option_surface.get_height()) // 2))

            if i < len(visible_options) - 1:
                pygame.draw.line(screen, (240, 240, 240), (x + 10, option_y + option_height), (x + width - 10, option_y + option_height), 1)

    if error and not is_open:
        error_surface = FONT_ERROR.render(error, True, RED)
        screen.blit(error_surface, (x + 5, input_y + field_height + 3))

    return input_rect, option_rects


def draw_search_field(screen, value, x, y, width, is_active, placeholder="Search..."):
    field_height = 40
    input_rect = pygame.Rect(x, y, width, field_height)

    border_color = BLUE if is_active else BORDER_COLOR

    pygame.draw.rect(screen, COLOR_WHITE, input_rect, border_radius=20)
    pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=20)

    icon_x = x + 15
    icon_y = y + field_height // 2
    pygame.draw.circle(screen, GREY, (icon_x, icon_y - 2), 6, 2)
    pygame.draw.line(screen, GREY, (icon_x + 4, icon_y + 2), (icon_x + 8, icon_y + 6), 2)

    text_x = x + 35

    if value:
        text_surface = FONT_BODY.render(value, True, COLOR_BLACK)
        screen.blit(text_surface, (text_x, y + (field_height - text_surface.get_height()) // 2))

        if is_active:
            cursor_x = text_x + text_surface.get_width() + 2
            pygame.draw.line(screen, COLOR_BLACK, (cursor_x, y + 10), (cursor_x, y + field_height - 10), 2)
    else:
        if is_active:
            pygame.draw.line(screen, COLOR_BLACK, (text_x, y + 10), (text_x, y + field_height - 10), 2)
        else:
            placeholder_surface = FONT_BODY.render(placeholder, True, GREY)
            screen.blit(placeholder_surface, (text_x, y + (field_height - placeholder_surface.get_height()) // 2))

    return input_rect