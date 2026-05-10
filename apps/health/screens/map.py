import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
GREEN = (52, 199, 89)
ORANGE = (255, 149, 0)

FONT_LARGE = pygame.font.SysFont("Arial", 32, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)


class MapScreen:

    def __init__(self):
        self.background_color = (245, 245, 250)

    def draw(self, screen):
        screen.fill(self.background_color)

        title = FONT_LARGE.render("Nearby", True, COLOR_BLACK)
        screen.blit(title, (20, 100))

        subtitle = FONT_BODY.render("Find health facilities near you", True, GREY)
        screen.blit(subtitle, (20, 145))

        map_y = 200
        map_height = 250
        map_surface = pygame.Surface((SCREEN_WIDTH - 40, map_height), pygame.SRCALPHA)
        pygame.draw.rect(map_surface, (220, 230, 220), (0, 0, SCREEN_WIDTH - 40, map_height), border_radius=15)
        screen.blit(map_surface, (20, map_y))
        pygame.draw.rect(screen, (200, 210, 200), (20, map_y, SCREEN_WIDTH - 40, map_height), 2, border_radius=15)

        map_text = FONT_BODY.render("🗺️ Map View", True, GREY)
        text_x = 20 + (SCREEN_WIDTH - 40 - map_text.get_width()) // 2
        text_y = map_y + (map_height - map_text.get_height()) // 2
        screen.blit(map_text, (text_x, text_y))

        self.draw_pin(screen, 100, map_y + 80, GREEN, "Hospital")
        self.draw_pin(screen, 250, map_y + 120, BLUE, "Pharmacy")
        self.draw_pin(screen, 180, map_y + 180, ORANGE, "Clinic")

        list_y = map_y + map_height + 30
        locations = [
            {"name": "City Hospital", "distance": "0.5 km", "type": "Hospital", "color": GREEN},
            {"name": "MedPharm", "distance": "0.8 km", "type": "Pharmacy", "color": BLUE},
            {"name": "Health Clinic", "distance": "1.2 km", "type": "Clinic", "color": ORANGE},
        ]

        for loc in locations:
            self.draw_location_item(screen, loc, 20, list_y)
            list_y += 70

    def draw_pin(self, screen, x, y, color, label=None):
        pygame.draw.circle(screen, color, (x, y), 12)
        pygame.draw.polygon(screen, color, [(x - 8, y + 5), (x + 8, y + 5), (x, y + 20)])
        pygame.draw.circle(screen, COLOR_WHITE, (x, y), 5)

        if label:
            label_text = FONT_SMALL.render(label, True, COLOR_BLACK)
            label_x = x - label_text.get_width() // 2
            label_y = y - 30

            padding = 4
            bg_rect = pygame.Rect(
                label_x - padding,
                label_y - padding,
                label_text.get_width() + padding * 2,
                label_text.get_height() + padding * 2
            )
            pygame.draw.rect(screen, COLOR_WHITE, bg_rect, border_radius=4)
            pygame.draw.rect(screen, (200, 200, 200), bg_rect, 1, border_radius=4)

            screen.blit(label_text, (label_x, label_y))

    def draw_location_item(self, screen, location, x, y):
        width = SCREEN_WIDTH - 40
        height = 60

        card_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(card_surface, (255, 255, 255, 255), (0, 0, width, height), border_radius=12)
        screen.blit(card_surface, (x, y))
        pygame.draw.rect(screen, (230, 230, 230), (x, y, width, height), 1, border_radius=12)

        if "color" in location:
            pygame.draw.circle(screen, location["color"], (x + 20, y + height // 2), 6)
            text_offset = 40
        else:
            text_offset = 15

        name_text = FONT_BODY.render(location["name"], True, COLOR_BLACK)
        screen.blit(name_text, (x + text_offset, y + 12))

        info_text = FONT_SMALL.render(f"{location['type']} • {location['distance']}", True, GREY)
        screen.blit(info_text, (x + text_offset, y + 35))

        arrow_text = FONT_BODY.render(">", True, GREY)
        screen.blit(arrow_text, (x + width - 25, y + 20))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pass
        return None