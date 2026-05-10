"""Dock drawing at the bottom of the screen."""
import pygame
import pygame.gfxdraw

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ICON_SIZE, COLOR_DOCK_BG, COLOR_WHITE, APP_GREEN, APP_BLUE, APP_DARK_GREY, APP_RED,
    FONT_WIDGET_SMALL
)
from utils import draw_rounded_rect
from .icons import draw_icon

def draw_dock(screen):
    """Draw the dock with app icons."""
    dock_height = 100
    dock_y = SCREEN_HEIGHT - dock_height - 25
    dock_margin = 20
    dock_x = dock_margin
    dock_width = SCREEN_WIDTH - (dock_margin * 2)

    draw_rounded_rect(
        screen,
        (dock_x, dock_y, dock_width, dock_height),
        COLOR_DOCK_BG, 0.4
    )

    num_icons = 4
    icon_spacing = (dock_width - (num_icons * ICON_SIZE)) / (num_icons + 1)

    def dock_icon_x(index):
        return int(dock_x + icon_spacing + index * (ICON_SIZE + icon_spacing))

    icon_y = dock_y + (dock_height - ICON_SIZE) // 2

    draw_icon(screen, dock_icon_x(0), icon_y, APP_GREEN, "", "message")
    draw_icon(screen, dock_icon_x(1), icon_y, APP_BLUE, "", "mail")
    draw_icon(screen, dock_icon_x(2), icon_y, (255, 255, 255), "", "health")
    draw_icon(screen, dock_icon_x(3), icon_y, APP_DARK_GREY, "", "camera")

    badge_x = int(dock_icon_x(1) + ICON_SIZE - 8)
    badge_y = int(icon_y - 2)

    pygame.gfxdraw.aacircle(screen, badge_x, badge_y, 10, APP_RED)
    pygame.gfxdraw.filled_circle(screen, badge_x, badge_y, 10, APP_RED)

    badge_num = FONT_WIDGET_SMALL.render("5", True, COLOR_WHITE)
    num_x = badge_x - badge_num.get_width() // 2
    num_y = badge_y - badge_num.get_height() // 2
    screen.blit(badge_num, (num_x, num_y))