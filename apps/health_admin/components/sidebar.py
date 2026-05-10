import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
SIDEBAR_BG = (28, 28, 30)

SIDEBAR_WIDTH = 70


class Sidebar:

    def __init__(self):
        self.tabs = [
            {"name": "dashboard", "icon": "📊", "label": "Home"},
            {"name": "doctors", "icon": "👨‍⚕️", "label": "Docs"},
            {"name": "patients", "icon": "🏥", "label": "Patients"},
            {"name": "appointments", "icon": "📅", "label": "Appts"},
            {"name": "reports", "icon": "📄", "label": "Reports"},
            {"name": "search", "icon": "🔍", "label": "Search"},
        ]
        self.bottom_tabs = [
            {"name": "logout", "icon": "🚪", "label": "Exit"}
        ]

        try:
            self.font_icon = pygame.font.SysFont("Segoe UI Emoji", 24)
        except:
            self.font_icon = pygame.font.SysFont("Arial", 24)

        self.font_label = pygame.font.SysFont("Arial", 10)

    def draw(self, screen, current_screen):
        sidebar_rect = pygame.Rect(0, 40, SIDEBAR_WIDTH, SCREEN_HEIGHT - 40)
        pygame.draw.rect(screen, SIDEBAR_BG, sidebar_rect)

        y = 60
        for tab in self.tabs:
            self._draw_tab(screen, tab, y, current_screen == tab["name"])
            y += 70

        y = SCREEN_HEIGHT - 80
        for tab in self.bottom_tabs:
            self._draw_tab(screen, tab, y, False)
            y += 70

    def _draw_tab(self, screen, tab, y, is_selected):
        if is_selected:
            indicator = pygame.Rect(0, y, 4, 60)
            pygame.draw.rect(screen, BLUE, indicator)

            highlight = pygame.Surface((SIDEBAR_WIDTH, 60), pygame.SRCALPHA)
            pygame.draw.rect(highlight, (255, 255, 255, 20), (0, 0, SIDEBAR_WIDTH, 60))
            screen.blit(highlight, (0, y))

        color = COLOR_WHITE if is_selected else GREY
        icon_surf = self.font_icon.render(tab["icon"], True, color)
        icon_x = (SIDEBAR_WIDTH - icon_surf.get_width()) // 2
        screen.blit(icon_surf, (icon_x, y + 10))

        label_surf = self.font_label.render(tab["label"], True, color)
        label_x = (SIDEBAR_WIDTH - label_surf.get_width()) // 2
        screen.blit(label_surf, (label_x, y + 40))

    def handle_click(self, pos):
        x, y = pos
        if x > SIDEBAR_WIDTH or y < 40:
            return None

        curr_y = 60
        for tab in self.tabs:
            if curr_y <= y < curr_y + 60:
                return tab["name"]
            curr_y += 70

        curr_y = SCREEN_HEIGHT - 80
        for tab in self.bottom_tabs:
            if curr_y <= y < curr_y + 60:
                return tab["name"]
            curr_y += 70

        return None