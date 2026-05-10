import pygame
import os
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
GREY = (142, 142, 147)

NAVBAR_HEIGHT = 70
ICON_SIZE = 28

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")


class BottomNavbar:

    def __init__(self):
        self.admin_tabs = [
            {"name": "home", "icon": "", "icon_file": "home_filled.png"},
            {"name": "doctors", "icon": "", "icon_file": "docreport.png"},
            {"name": "patients", "icon": "", "icon_file": "patientreport.png"},
            {"name": "appointments", "icon": "", "icon_file": "appointmentsreport.png"},
            {"name": "reports", "icon": "", "icon_file": "statisticsreport.png"},
        ]

        # Doctor tabs (only 3)
        self.doctor_tabs = [
            {"name": "home", "icon": "", "icon_file": "home_filled.png"},
            {"name": "appointments", "icon": "", "icon_file": "appointmentsreport.png"},
            {"name": "patients", "icon": "", "icon_file": "patientreport.png"},
        ]

        self.tabs = self.doctor_tabs
        self.is_admin_mode = False
        self.selected_tab = 0
        self.icon_cache = {}

        try:
            self.font_icon = pygame.font.SysFont("Segoe UI Emoji", 24)
        except:
            self.font_icon = pygame.font.SysFont("Arial", 24)

        self.load_icons()

    def set_admin_mode(self, is_admin):
        self.is_admin_mode = is_admin
        self.tabs = self.admin_tabs if is_admin else self.doctor_tabs
        self.selected_tab = 0

    def load_icons(self):
        icon_files = [
            "home_filled.png",
            "docreport.png",
            "patientreport.png",
            "appointmentsreport.png",
            "statisticsreport.png",
        ]

        for icon_file in icon_files:
            icon_path = os.path.join(ICON_DIR, icon_file)
            if os.path.exists(icon_path):
                try:
                    icon = pygame.image.load(icon_path).convert_alpha()
                    self.icon_cache[icon_file] = pygame.transform.smoothscale(icon, (ICON_SIZE, ICON_SIZE))
                except (pygame.error, OSError):
                    pass

    def draw(self, screen):
        navbar_y = SCREEN_HEIGHT - NAVBAR_HEIGHT

        navbar_surface = pygame.Surface((SCREEN_WIDTH, NAVBAR_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(navbar_surface, (255, 255, 255, 250), (0, 0, SCREEN_WIDTH, NAVBAR_HEIGHT))
        screen.blit(navbar_surface, (0, navbar_y))

        pygame.draw.line(screen, (220, 220, 220), (0, navbar_y), (SCREEN_WIDTH, navbar_y), 1)

        tab_count = len(self.tabs)
        tab_width = SCREEN_WIDTH // tab_count

        for i, tab in enumerate(self.tabs):
            is_selected = (i == self.selected_tab)
            tab_center_x = (i * tab_width) + (tab_width // 2)
            icon_y = navbar_y + 18
            color = BLUE if is_selected else GREY

            icon_file = tab.get("icon_file")
            if icon_file and icon_file in self.icon_cache:
                icon = self.icon_cache[icon_file]
                tinted = self.tint_icon(icon, color)
                icon_rect = tinted.get_rect(center=(tab_center_x, icon_y + ICON_SIZE // 2))
                screen.blit(tinted, icon_rect)
            else:
                icon_surface = self.font_icon.render(tab["icon"], True, color)
                icon_rect = icon_surface.get_rect(center=(tab_center_x, icon_y + ICON_SIZE // 2))
                screen.blit(icon_surface, icon_rect)

        indicator_width = 134
        indicator_height = 5
        indicator_x = (SCREEN_WIDTH - indicator_width) // 2
        indicator_y = SCREEN_HEIGHT - 12
        pygame.draw.rect(screen, COLOR_BLACK, (indicator_x, indicator_y, indicator_width, indicator_height), border_radius=3)

    def tint_icon(self, icon, color):
        result = pygame.Surface(icon.get_size(), pygame.SRCALPHA)
        result.blit(icon, (0, 0))

        overlay = pygame.Surface(icon.get_size(), pygame.SRCALPHA)
        overlay.fill((*color, 255))
        result.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        for x in range(icon.get_width()):
            for y in range(icon.get_height()):
                alpha = icon.get_at((x, y))[3]
                if alpha > 0:
                    r, g, b, _ = result.get_at((x, y))
                    result.set_at((x, y), (r, g, b, alpha))
                else:
                    result.set_at((x, y), (0, 0, 0, 0))

        return result

    def handle_click(self, pos):
        x, y = pos
        navbar_y = SCREEN_HEIGHT - NAVBAR_HEIGHT

        if y > navbar_y:
            tab_count = len(self.tabs)
            tab_width = SCREEN_WIDTH // tab_count

            clicked_tab = x // tab_width
            if 0 <= clicked_tab < tab_count:
                self.selected_tab = clicked_tab
                return True

        return False

    def get_selected_tab_name(self):
        return self.tabs[self.selected_tab]["name"]

    def set_selected_tab(self, tab_name):
        for i, tab in enumerate(self.tabs):
            if tab["name"] == tab_name:
                self.selected_tab = i
                break