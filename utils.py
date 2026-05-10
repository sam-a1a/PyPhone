"""Utility drawing functions."""
import pygame
from config import SCREEN_WIDTH

def draw_gradient_background(surface):
    """Draws the sunset gradient (Cyan -> Orange -> Purple)."""
    height = surface.get_height()

    for y in range(height):
        if y < height * 0.4:
            r, g, b = (0, 180, 210)
        elif y < height * 0.7:
            ratio = (y - height * 0.4) / (height * 0.3)
            r = int(0 + (255 - 0) * ratio)
            g = int(180 + (100 - 180) * ratio)
            b = int(210 + (50 - 210) * ratio)
        else:
            ratio = (y - height * 0.7) / (height * 0.3)
            r = int(255 + (50 - 255) * ratio)
            g = int(100 + (20 - 100) * ratio)
            b = int(50 + (50 - 50) * ratio)

        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

def draw_rounded_rect(surface, rect, color, radius=0.4):
    """Draw a rectangle with rounded corners."""
    rect = pygame.Rect(rect)
    color = pygame.Color(*color)
    alpha = color.a
    color.a = 0
    pos = rect.topleft
    rect.topleft = 0, 0
    rectangle = pygame.Surface(rect.size, pygame.SRCALPHA)

    circle = pygame.Surface([min(rect.size) * 3] * 2, pygame.SRCALPHA)
    pygame.draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
    circle = pygame.transform.smoothscale(
        circle, [int(min(rect.size) * radius)] * 2
    )

    radius_rect = rectangle.blit(circle, (0, 0))
    radius_rect.bottomright = rect.bottomright
    rectangle.blit(circle, radius_rect)
    radius_rect.topright = rect.topright
    rectangle.blit(circle, radius_rect)
    radius_rect.bottomleft = rect.bottomleft
    rectangle.blit(circle, radius_rect)

    rectangle.fill((0, 0, 0), rect.inflate(-radius_rect.w, 0))
    rectangle.fill((0, 0, 0), rect.inflate(0, -radius_rect.h))

    rectangle.fill(color, special_flags=pygame.BLEND_RGBA_MAX)
    rectangle.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)

    surface.blit(rectangle, pos)