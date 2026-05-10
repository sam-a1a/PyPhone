import os

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")

BLUE = (0, 122, 255)
GREY = (142, 142, 147)

NAVBAR_HEIGHT = 85
ICON_SIZE = 28


class BottomNavbar:

    def __init__(self):
        self.tabs = [
            {"name": "home", "has_variants": True},
            {"name": "book", "has_variants": True},
            {"name": "history", "has_variants": False},
            {"name": "map", "has_variants": True},
        ]
        self.selected_tab = 0
        self.icon_cache = {}
        self.load_icons()

    def load_icons(self):
        for tab in self.tabs:
            name = tab["name"]
            has_variants = tab["has_variants"]

            if has_variants:
                filled_path = os.path.join(ICON_DIR, f"{name}_filled.png")
                if os.path.exists(filled_path):
                    try:
                        icon = pygame.image.load(filled_path).convert_alpha()
                        self.icon_cache[f"{name}_filled"] = pygame.transform.smoothscale(icon, (ICON_SIZE, ICON_SIZE))
                    except (pygame.error, OSError):
                        pass

                outlined_path = os.path.join(ICON_DIR, f"{name}_outlined.png")
                if os.path.exists(outlined_path):
                    try:
                        icon = pygame.image.load(outlined_path).convert_alpha()
                        self.icon_cache[f"{name}_outlined"] = pygame.transform.smoothscale(icon, (ICON_SIZE, ICON_SIZE))
                    except (pygame.error, OSError):
                        pass
            else:
                icon_path = os.path.join(ICON_DIR, f"{name}.png")
                if os.path.exists(icon_path):
                    try:
                        icon = pygame.image.load(icon_path).convert_alpha()
                        self.icon_cache[name] = pygame.transform.smoothscale(icon, (ICON_SIZE, ICON_SIZE))
                    except (pygame.error, OSError):
                        pass

    def get_icon(self, tab_index, is_selected):
        tab = self.tabs[tab_index]
        name = tab["name"]
        has_variants = tab["has_variants"]

        if has_variants:
            key = f"{name}_filled" if is_selected else f"{name}_outlined"
        else:
            key = name

        return self.icon_cache.get(key)

    def draw(self, screen):
        navbar_y = SCREEN_HEIGHT - NAVBAR_HEIGHT

        navbar_surface = pygame.Surface((SCREEN_WIDTH, NAVBAR_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(navbar_surface, (255, 255, 255, 245), (0, 0, SCREEN_WIDTH, NAVBAR_HEIGHT))
        screen.blit(navbar_surface, (0, navbar_y))

        pygame.draw.line(screen, (220, 220, 220), (0, navbar_y), (SCREEN_WIDTH, navbar_y), 1)

        tab_count = len(self.tabs)
        tab_width = SCREEN_WIDTH // tab_count

        for i, tab in enumerate(self.tabs):
            is_selected = (i == self.selected_tab)

            tab_center_x = (i * tab_width) + (tab_width // 2)
            icon_y = navbar_y + 18

            icon = self.get_icon(i, is_selected)
            if icon:
                icon_copy = icon.copy()
                if is_selected:
                    tinted = self.tint_icon(icon_copy, BLUE)
                    icon_rect = tinted.get_rect(center=(tab_center_x, icon_y + ICON_SIZE // 2))
                    screen.blit(tinted, icon_rect)
                else:
                    tinted = self.tint_icon(icon_copy, GREY)
                    icon_rect = tinted.get_rect(center=(tab_center_x, icon_y + ICON_SIZE // 2))
                    screen.blit(tinted, icon_rect)
            else:
                color = BLUE if is_selected else GREY
                pygame.draw.circle(screen, color, (tab_center_x, icon_y + ICON_SIZE // 2), ICON_SIZE // 2 - 2)

        indicator_width = 134
        indicator_height = 5
        indicator_x = (SCREEN_WIDTH - indicator_width) // 2
        indicator_y = SCREEN_HEIGHT - 15
        pygame.draw.rect(screen, COLOR_BLACK, (indicator_x, indicator_y, indicator_width, indicator_height), border_radius=3)

    def tint_icon(self, icon, color):
        tinted = icon.copy()
        tinted.fill((*color, 0), special_flags=pygame.BLEND_RGB_ADD)

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