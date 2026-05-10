import pygame
from config import COLOR_WHITE, COLOR_BLACK

HEADER_BG = (245, 245, 247)
ROW_BG = COLOR_WHITE
ROW_ALT_BG = (250, 250, 252)
BORDER_COLOR = (230, 230, 230)
BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)

FONT_HEADER = pygame.font.SysFont("Arial", 12, bold=True)
FONT_CELL = pygame.font.SysFont("Arial", 12)
FONT_BUTTON = pygame.font.SysFont("Arial", 11)


def draw_table(screen, headers, rows, x, y, width, row_height=40,
               col_widths=None, max_rows=8):
    action_buttons = []

    num_cols = len(headers)
    if col_widths is None:
        col_widths = [1] * num_cols

    total_proportion = sum(col_widths)
    actual_widths = [int(width * (w / total_proportion)) for w in col_widths]

    header_rect = pygame.Rect(x, y, width, row_height)
    pygame.draw.rect(screen, HEADER_BG, header_rect)
    pygame.draw.line(screen, BORDER_COLOR, (x, y + row_height),
                     (x + width, y + row_height), 1)

    col_x = x
    for i, header in enumerate(headers):
        header_surface = FONT_HEADER.render(header, True, (100, 100, 100))
        screen.blit(header_surface, (col_x + 10, y + (row_height - header_surface.get_height()) // 2))
        col_x += actual_widths[i]

    for row_idx, row in enumerate(rows[:max_rows]):
        row_y = y + row_height * (row_idx + 1)
        row_bg = ROW_BG if row_idx % 2 == 0 else ROW_ALT_BG

        row_rect = pygame.Rect(x, row_y, width, row_height)
        pygame.draw.rect(screen, row_bg, row_rect)
        pygame.draw.line(screen, BORDER_COLOR, (x, row_y + row_height),
                         (x + width, row_y + row_height), 1)

        col_x = x
        for col_idx, cell in enumerate(row):
            if isinstance(cell, dict) and cell.get("type") == "actions":
                btn_x = col_x + 5
                for action in cell.get("actions", []):
                    btn_width = 50
                    btn_height = 26
                    btn_y = row_y + (row_height - btn_height) // 2

                    if action["name"] == "edit":
                        btn_color = BLUE
                    elif action["name"] == "delete":
                        btn_color = RED
                    elif action["name"] == "view":
                        btn_color = GREEN
                    else:
                        btn_color = (100, 100, 100)

                    btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
                    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=6)

                    btn_text = FONT_BUTTON.render(action["label"], True, COLOR_WHITE)
                    text_x = btn_x + (btn_width - btn_text.get_width()) // 2
                    text_y = btn_y + (btn_height - btn_text.get_height()) // 2
                    screen.blit(btn_text, (text_x, text_y))

                    action_buttons.append({
                        "rect": btn_rect,
                        "action": action["name"],
                        "row_id": cell.get("row_id")
                    })

                    btn_x += btn_width + 5
            else:
                cell_text = str(cell) if cell else ""
                if len(cell_text) > 20:
                    cell_text = cell_text[:18] + "..."

                cell_surface = FONT_CELL.render(cell_text, True, COLOR_BLACK)
                screen.blit(cell_surface, (col_x + 10, row_y + (row_height - cell_surface.get_height()) // 2))

            col_x += actual_widths[col_idx]

    return action_buttons


def draw_table_row(screen, cells, x, y, width, height, col_widths, is_header=False, is_alt=False):

    if is_header:
        bg_color = HEADER_BG
    elif is_alt:
        bg_color = ROW_ALT_BG
    else:
        bg_color = ROW_BG

    row_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, bg_color, row_rect)
    pygame.draw.line(screen, BORDER_COLOR, (x, y + height), (x + width, y + height), 1)

    font = FONT_HEADER if is_header else FONT_CELL
    text_color = (100, 100, 100) if is_header else COLOR_BLACK

    col_x = x
    for i, cell in enumerate(cells):
        cell_text = str(cell) if cell else ""
        cell_surface = font.render(cell_text, True, text_color)
        screen.blit(cell_surface, (col_x + 10, y + (height - cell_surface.get_height()) // 2))
        col_x += col_widths[i]