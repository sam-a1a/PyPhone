"""Configuration constants for the iPhone home screen."""
import pygame

pygame.init()

SCREEN_WIDTH = 420
SCREEN_HEIGHT = 850
CORNER_RADIUS = 40

ICON_SIZE = 60
ICON_RADIUS = 14
GRID_START_Y = 110
COL_SPACING = 25
ROW_SPACING = 35
MARGIN_X = 52  # Centered: (420 - (4*60 + 3*25)) / 2 = 52

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_OFF_WHITE = (245, 245, 245)
COLOR_GREY_TEXT = (200, 200, 200)
COLOR_DOCK_BG = (255, 255, 255, 50)
COLOR_WIDGET_BG = (30, 30, 40, 180)

APP_GREEN = (52, 199, 89)
APP_BLUE = (0, 122, 255)
APP_RED = (255, 59, 48)
APP_ORANGE = (255, 149, 0)
APP_GREY = (142, 142, 147)
APP_DARK_GREY = (44, 44, 46)
APP_WEATHER_BLUE = (40, 110, 200)

try:
    FONT_TIME = pygame.font.SysFont("Arial", 16, bold=True)
    FONT_ICON = pygame.font.SysFont("Arial", 11)
    FONT_WIDGET_BIG = pygame.font.SysFont("Arial", 36)
    FONT_WIDGET_MED = pygame.font.SysFont("Arial", 14, bold=True)
    FONT_WIDGET_SMALL = pygame.font.SysFont("Arial", 10)
except (pygame.error, FileNotFoundError, OSError) as e:
    print(f"Font loading failed: {e}, using defaults")
    FONT_TIME = pygame.font.Font(None, 20)
    FONT_ICON = pygame.font.Font(None, 16)
    FONT_WIDGET_BIG = pygame.font.Font(None, 40)
    FONT_WIDGET_MED = pygame.font.Font(None, 18)
    FONT_WIDGET_SMALL = pygame.font.Font(None, 14)