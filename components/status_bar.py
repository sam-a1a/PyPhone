"""Status bar drawing - iOS style."""
import pygame
import pygame.gfxdraw
from datetime import datetime
from config import SCREEN_WIDTH, COLOR_WHITE, COLOR_BLACK, FONT_TIME

def draw_status_bar(screen, dark_mode=True):
    """Draw the top status bar with time, notch, and indicators.

    Args:
        screen: Pygame surface to draw on
        dark_mode: If True, white text. If False, black text (for light backgrounds)
    """

    # Choose text color based on mode
    if dark_mode:
        text_color = COLOR_WHITE
    else:
        text_color = COLOR_BLACK

    # Get real system time
    try:
        current_time = datetime.now().strftime("%-I:%M")  # Mac/Linux
    except ValueError:
        current_time = datetime.now().strftime("%#I:%M")  # Windows

    # Time (left side)
    font = pygame.font.SysFont("Arial", 16, bold=True)
    time_surf = font.render(current_time, True, text_color)
    screen.blit(time_surf, (45, 15))

    # Dynamic Island (Notch) - always black
    _draw_dynamic_island(screen)

    # Right side indicators (from right to left)
    x_offset = SCREEN_WIDTH - 25

    # Battery
    x_offset = _draw_battery(screen, x_offset, 17, 85, text_color)

    # Cellular Signal
    x_offset = _draw_signal_bars(screen, x_offset - 8, 16, text_color)


def _draw_dynamic_island(screen):
    """Draw the Dynamic Island (pill-shaped notch)."""
    island_width = 100
    island_height = 30
    island_x = SCREEN_WIDTH // 2 - island_width // 2
    island_y = 12

    # Create surface for smooth drawing
    island_surf = pygame.Surface((island_width, island_height), pygame.SRCALPHA)

    radius = island_height // 2

    # Draw rounded ends
    pygame.gfxdraw.aacircle(island_surf, radius, radius, radius - 1, COLOR_BLACK)
    pygame.gfxdraw.filled_circle(island_surf, radius, radius, radius - 1, COLOR_BLACK)

    pygame.gfxdraw.aacircle(island_surf, island_width - radius, radius, radius - 1, COLOR_BLACK)
    pygame.gfxdraw.filled_circle(island_surf, island_width - radius, radius, radius - 1, COLOR_BLACK)

    # Draw middle rectangle
    pygame.draw.rect(island_surf, COLOR_BLACK, (radius, 0, island_width - 2 * radius, island_height))

    screen.blit(island_surf, (island_x, island_y))


def _draw_battery(screen, x, y, charge_percent, text_color):
    """Draw iOS-style battery indicator."""
    width = 24
    height = 11
    border_radius = 3
    nub_width = 2
    nub_height = 4
    border_width = 1

    batt_x = x - width - nub_width
    batt_y = y

    batt_surf = pygame.Surface((width + nub_width + 2, height + 2), pygame.SRCALPHA)

    # Draw battery outline
    outline_rect = pygame.Rect(0, 0, width, height)
    pygame.draw.rect(batt_surf, text_color, outline_rect, border_width, border_radius)

    # Draw battery nub
    nub_x = width
    nub_y = (height - nub_height) // 2
    pygame.draw.rect(batt_surf, text_color, (nub_x, nub_y, nub_width + 1, nub_height), border_radius=1)

    # Draw charge level
    padding = 2
    max_fill_width = width - padding * 2 - border_width
    fill_width = int(max_fill_width * charge_percent / 100)
    fill_height = height - padding * 2 - border_width

    if charge_percent <= 20:
        fill_color = (255, 59, 48)  # Red
    elif charge_percent <= 50:
        fill_color = (255, 204, 0)  # Yellow
    else:
        fill_color = (52, 199, 89)  # Green

    if fill_width > 0:
        fill_rect = pygame.Rect(padding, padding, fill_width, fill_height)
        pygame.draw.rect(batt_surf, fill_color, fill_rect, border_radius=2)

    screen.blit(batt_surf, (batt_x, batt_y))

    return batt_x


def _draw_signal_bars(screen, x, y, text_color):
    """Draw iOS-style cellular signal bars."""
    num_bars = 4
    bar_width = 3
    bar_spacing = 2
    max_height = 12
    min_height = 3

    active_bars = 3

    total_width = num_bars * bar_width + (num_bars - 1) * bar_spacing
    start_x = x - total_width

    for i in range(num_bars):
        bar_height = min_height + int((max_height - min_height) * (i / (num_bars - 1)))

        bar_x = start_x + i * (bar_width + bar_spacing)
        bar_y = y + (max_height - bar_height)

        if i < active_bars:
            color = text_color
        else:
            # Dim color
            if text_color == COLOR_WHITE:
                color = (255, 255, 255, 80)
            else:
                color = (0, 0, 0, 80)

        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, color, bar_rect, border_radius=1)

    return start_x