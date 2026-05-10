import pygame
import math
from config import COLOR_BLACK

FONT_LARGE = pygame.font.SysFont("Arial", 36, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 12)

def draw_card(screen, x, y, width, height, title, value, unit, color, subtitle):
    card_rect = pygame.Rect(x, y, width, height)
    card_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surface, (255, 255, 255, 255),
                    (0, 0, width, height), border_radius=15)
    screen.blit(card_surface, (x, y))

    pygame.draw.rect(screen, (230, 230, 230), card_rect, 1, border_radius=15)
    pygame.draw.rect(screen, color, (x + 15, y + 15, 4, 30), border_radius=2)

    title_text = FONT_MEDIUM.render(title, True, COLOR_BLACK)
    screen.blit(title_text, (x + 30, y + 15))

    sub_text = FONT_TINY.render(subtitle, True, (120, 120, 120))
    screen.blit(sub_text, (x + 30, y + 38))

    value_text = FONT_LARGE.render(value, True, color)
    screen.blit(value_text, (x + width - 120, y + 30))

    unit_text = FONT_SMALL.render(unit, True, (100, 100, 100))
    screen.blit(unit_text, (x + width - 50, y + 45))

def draw_activity_ring(screen, center, radius, color, progress):
    pygame.draw.circle(screen, (220, 220, 220), center, radius, 8)

    if progress > 0:
        num_segments = int(50 * progress)
        for i in range(num_segments):
            angle = (math.pi / 2) - (2 * math.pi * progress * i / num_segments)
            x1 = center[0] + int((radius - 4) * math.cos(angle))
            y1 = center[1] - int((radius - 4) * math.sin(angle))
            x2 = center[0] + int((radius + 4) * math.cos(angle))
            y2 = center[1] - int((radius + 4) * math.sin(angle))
            pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)