import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database

BLUE = (0, 122, 255)
GREEN = (52, 199, 89)
PURPLE = (175, 82, 222)
ORANGE = (255, 149, 0)
GREY = (142, 142, 147)
LIGHT_BG = (245, 245, 250)

FONT_LARGE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 12)

NAVBAR_HEIGHT = 85


class SearchScreen:
    def __init__(self):
        self.db = Database()
        self.background_color = LIGHT_BG
        self.query = ""
        self.search_active = True
        self.doctors_results = []
        self.patients_results = []
        self.scroll_y = 0
        self.button_rects = {}
        self.result_cards = []
        pygame.key.set_repeat(400, 50)

    def reset(self):
        self.query = ""
        self.search_active = True
        self.doctors_results = []
        self.patients_results = []
        self.scroll_y = 0

    def perform_search(self):
        if not self.query:
            self.doctors_results = []
            self.patients_results = []
            return

        self.doctors_results = self.db.search_doctors(self.query)[:5]
        self.patients_results = self.db.search_patients(self.query)[:5]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if "search" in self.button_rects:
                self.search_active = self.button_rects["search"].collidepoint(x, y)

            for card_rect, result_type, result_id in self.result_cards:
                if card_rect.collidepoint(x, y):
                    if result_type == "doctor":
                        return f"view_doctor_{result_id}"
                    elif result_type == "patient":
                        return f"view_patient_{result_id}"

        elif event.type == pygame.KEYDOWN:
            if self.search_active:
                if event.key == pygame.K_BACKSPACE:
                    self.query = self.query[:-1]
                    self.perform_search()
                elif event.key == pygame.K_RETURN:
                    self.search_active = False
                elif event.key == pygame.K_ESCAPE:
                    self.query = ""
                    self.perform_search()
                elif event.unicode and event.unicode.isprintable():
                    self.query += event.unicode
                    self.perform_search()

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            self.scroll_y = max(0, min(300, self.scroll_y))

        return None

    def update(self):
        pass

    def draw(self, screen):
        screen.fill(self.background_color)

        self.button_rects = {}
        self.result_cards = []

        title = FONT_LARGE.render("Search", True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        search_y = 100
        search_rect = self.draw_search_field(screen, 15, search_y, SCREEN_WIDTH - 30)
        self.button_rects["search"] = search_rect

        content_y = 160 - self.scroll_y

        if not self.query:
            hint_y = 250
            hint_text = FONT_BODY.render("Search for doctors or patients", True, GREY)
            screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, hint_y))
            return

        if not self.doctors_results and not self.patients_results:
            hint_y = 250
            hint_text = FONT_BODY.render("No results found", True, GREY)
            screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, hint_y))
            return

        if self.doctors_results:
            if content_y > 100:
                section_title = FONT_MEDIUM.render(f"Doctors ({len(self.doctors_results)})", True, COLOR_BLACK)
                screen.blit(section_title, (20, content_y))
            content_y += 35

            for i, doctor in enumerate(self.doctors_results):
                card_y = content_y + (i * 70)
                if 100 < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 20:
                    card_rect = self.draw_result_card(screen, "doctor", doctor, 15, card_y, i)
                    self.result_cards.append((card_rect, "doctor", doctor.id))
            content_y += len(self.doctors_results) * 70 + 20

        if self.patients_results:
            if content_y > 100:
                section_title = FONT_MEDIUM.render(f"Patients ({len(self.patients_results)})", True, COLOR_BLACK)
                screen.blit(section_title, (20, content_y))
            content_y += 35

            for i, patient in enumerate(self.patients_results):
                card_y = content_y + (i * 70)
                if 100 < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 20:
                    card_rect = self.draw_result_card(screen, "patient", patient, 15, card_y, i)
                    self.result_cards.append((card_rect, "patient", patient.id))

    def draw_search_field(self, screen, x, y, width):
        height = 48
        rect = pygame.Rect(x, y, width, height)

        pygame.draw.rect(screen, COLOR_WHITE, rect, border_radius=14)
        border_color = BLUE if self.search_active else (220, 220, 220)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=14)

        icon_x = x + 18
        icon_y = y + height // 2
        pygame.draw.circle(screen, GREY, (icon_x, icon_y - 2), 9, 2)
        pygame.draw.line(screen, GREY, (icon_x + 6, icon_y + 4), (icon_x + 12, icon_y + 10), 2)

        text_x = x + 42
        if self.query:
            text_surface = FONT_BODY.render(self.query, True, COLOR_BLACK)
            screen.blit(text_surface, (text_x, y + (height - text_surface.get_height()) // 2))

            if self.search_active:
                cursor_x = text_x + text_surface.get_width() + 2
                pygame.draw.line(screen, COLOR_BLACK, (cursor_x, y + 12), (cursor_x, y + height - 12), 2)
        else:
            if self.search_active:
                pygame.draw.line(screen, COLOR_BLACK, (text_x, y + 12), (text_x, y + height - 12), 2)
            else:
                placeholder = FONT_BODY.render("Search doctors, patients...", True, GREY)
                screen.blit(placeholder, (text_x, y + (height - placeholder.get_height()) // 2))

        return rect

    def draw_result_card(self, screen, result_type, item, x, y, index):
        width = SCREEN_WIDTH - 30
        height = 65

        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=12)

        colors = [BLUE, GREEN, PURPLE, ORANGE]
        avatar_color = colors[index % len(colors)]
        avatar_x = x + 30
        avatar_y = y + height // 2
        pygame.draw.circle(screen, avatar_color, (avatar_x, avatar_y), 20)

        initial = item.name[0].upper() if item.name else "?"
        initial_font = pygame.font.SysFont("Arial", 14, bold=True)
        initial_surface = initial_font.render(initial, True, COLOR_WHITE)
        screen.blit(initial_surface, (avatar_x - initial_surface.get_width() // 2,
                                       avatar_y - initial_surface.get_height() // 2))

        name_text = FONT_BODY.render(item.name, True, COLOR_BLACK)
        screen.blit(name_text, (x + 65, y + 12))

        if result_type == "doctor":
            subtitle = item.specialty or "Doctor"
            badge_color = BLUE
        else:
            subtitle = item.disease or "Patient"
            badge_color = GREEN

        subtitle_text = FONT_SMALL.render(subtitle, True, GREY)
        screen.blit(subtitle_text, (x + 65, y + 38))

        badge_x = x + width - 70
        badge_y = y + (height - 22) // 2
        pygame.draw.rect(screen, (*badge_color, 30), (badge_x, badge_y, 55, 22), border_radius=11)
        type_text = FONT_TINY.render(result_type.title(), True, badge_color)
        screen.blit(type_text, (badge_x + 27 - type_text.get_width() // 2, badge_y + 4))

        return card_rect