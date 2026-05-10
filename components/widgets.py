"""Widget drawing functions."""
import pygame
import math
from config import (
    SCREEN_WIDTH, ICON_SIZE, ROW_SPACING,
    COLOR_WHITE, APP_WEATHER_BLUE,
    FONT_WIDGET_BIG, FONT_WIDGET_MED, FONT_WIDGET_SMALL
)

def draw_weather_widget(screen, y_row):
    """Full width weather widget, 20dp corners, below the given row."""

    margin = 32
    x = margin
    width = SCREEN_WIDTH - (margin * 2)
    height = 140
    radius = 20

    # Position below the given row (y_row is the y position of the last icon row)
    y = y_row + ICON_SIZE + ROW_SPACING

    # Simple rounded rectangle
    pygame.draw.rect(screen, APP_WEATHER_BLUE, (x, y, width, height), border_radius=radius)

    # Text
    screen.blit(FONT_WIDGET_MED.render("Damascus", True, COLOR_WHITE), (x+20, y+20))
    screen.blit(FONT_WIDGET_BIG.render("22°", True, COLOR_WHITE), (x+20, y+45))
    screen.blit(FONT_WIDGET_SMALL.render("Nighty!", True, COLOR_WHITE), (x+20, y+height-45))
    screen.blit(FONT_WIDGET_SMALL.render("H:27°  L:16°", True, COLOR_WHITE), (x+20, y+height-25))

    # Sun
    sun_x = x + width - 60
    sun_y = y + 55
    pygame.draw.circle(screen, (255, 215, 0), (sun_x, sun_y), 25)
    for a in range(0, 360, 45):
        r = math.radians(a)
        pygame.draw.line(screen, (255, 230, 100),
            (sun_x + int(math.cos(r) * 28), sun_y + int(math.sin(r) * 28)),
            (sun_x + int(math.cos(r) * 38), sun_y + int(math.sin(r) * 38)), 3)