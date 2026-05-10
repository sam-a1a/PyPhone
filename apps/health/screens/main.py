import pygame
from datetime import datetime
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE
from apps.health.components import draw_card, draw_activity_ring
from apps.shared import Database

BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
ORANGE = (255, 149, 0)
PINK = (255, 45, 85)
PURPLE = (175, 82, 222)
GREY = (142, 142, 147)

FONT_LARGE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)


class MainScreen:

    def __init__(self):
        self.background_color = (245, 245, 250)
        self.db = Database()

        self.current_patient_id = 1

        self.steps_today = 8432
        self.steps_goal = 10000
        self.heart_rate = 72
        self.calories_burned = 385
        self.sleep_hours = 7.5

        self.scroll_y = 0

    def get_upcoming_appointments(self):
        appointments = self.db.get_appointments_by_patient(self.current_patient_id)
        return [a for a in appointments if a.status == 'scheduled']

    def draw(self, screen):
        screen.fill(self.background_color)

        title = FONT_LARGE.render("Welcome Back!", True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        today = datetime.now().strftime("%A, %B %d")
        date_text = FONT_SMALL.render(today, True, GREY)
        screen.blit(date_text, (20, 90))

        self.draw_stats_card(screen, 20, 125)

        upcoming = self.get_upcoming_appointments()
        self.draw_upcoming_section(screen, 20, 270, upcoming)

        ring_y = 520 if len(upcoming) > 1 else 450
        if ring_y - self.scroll_y < SCREEN_HEIGHT - 200:
            self.draw_activity_section(screen, ring_y - self.scroll_y)

    def draw_stats_card(self, screen, x, y):
        width = SCREEN_WIDTH - 40
        height = 130

        card_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(card_surface, (255, 255, 255, 255), (0, 0, width, height), border_radius=15)
        screen.blit(card_surface, (x, y))
        pygame.draw.rect(screen, (230, 230, 230), (x, y, width, height), 1, border_radius=15)

        stats = [
            {"label": "Heart Rate", "value": f"{self.heart_rate}", "unit": "BPM", "color": RED},
            {"label": "Calories", "value": f"{self.calories_burned}", "unit": "kcal", "color": ORANGE},
            {"label": "Sleep", "value": f"{self.sleep_hours}", "unit": "hrs", "color": PURPLE},
        ]

        stat_width = width // 3
        for i, stat in enumerate(stats):
            stat_x = x + (i * stat_width) + stat_width // 2

            value_text = FONT_MEDIUM.render(stat["value"], True, stat["color"])
            screen.blit(value_text, (stat_x - value_text.get_width() // 2, y + 30))

            unit_text = FONT_SMALL.render(stat["unit"], True, GREY)
            screen.blit(unit_text, (stat_x - unit_text.get_width() // 2, y + 55))

            label_text = FONT_SMALL.render(stat["label"], True, GREY)
            screen.blit(label_text, (stat_x - label_text.get_width() // 2, y + 85))

    def draw_upcoming_section(self, screen, x, y, appointments):
        header_text = FONT_MEDIUM.render("Upcoming Appointments", True, COLOR_BLACK)
        screen.blit(header_text, (x, y))

        count = len(appointments)
        if count > 0:
            count_text = FONT_SMALL.render(str(count), True, COLOR_WHITE)
            badge_x = x + header_text.get_width() + 10
            badge_width = max(24, count_text.get_width() + 12)
            pygame.draw.rect(screen, BLUE, (badge_x, y + 2, badge_width, 20), border_radius=10)
            screen.blit(count_text, (badge_x + badge_width // 2 - count_text.get_width() // 2, y + 4))

        card_y = y + 35

        if not appointments:
            width = SCREEN_WIDTH - 40
            pygame.draw.rect(screen, COLOR_WHITE, (x, card_y, width, 80), border_radius=15)
            pygame.draw.rect(screen, (230, 230, 230), (x, card_y, width, 80), 1, border_radius=15)

            no_appt = FONT_BODY.render("No upcoming appointments", True, GREY)
            screen.blit(no_appt, (x + width // 2 - no_appt.get_width() // 2, card_y + 20))

            book_text = FONT_SMALL.render("Tap 'Book' to schedule one", True, BLUE)
            screen.blit(book_text, (x + width // 2 - book_text.get_width() // 2, card_y + 48))
        else:
            for i, appt in enumerate(appointments[:3]):
                self.draw_appointment_card(screen, appt, x, card_y + (i * 75))

            if count > 3:
                more_y = card_y + (3 * 75)
                more_text = FONT_SMALL.render(f"+ {count - 3} more appointments", True, BLUE)
                screen.blit(more_text, (x + (SCREEN_WIDTH - 40) // 2 - more_text.get_width() // 2, more_y))

    def draw_appointment_card(self, screen, appt, x, y):
        width = SCREEN_WIDTH - 40
        height = 70

        pygame.draw.rect(screen, BLUE, (x, y, width, height), border_radius=12)

        doctor_text = FONT_MEDIUM.render(f"Dr. {appt.doctor_name}", True, COLOR_WHITE)
        screen.blit(doctor_text, (x + 15, y + 12))

        spec_text = FONT_SMALL.render(appt.doctor_specialty, True, (200, 220, 255))
        screen.blit(spec_text, (x + 15, y + 35))

        if appt.appointment_date:
            date_str = appt.appointment_date.strftime("%b %d")
            datetime_text = FONT_SMALL.render(f"{date_str}", True, COLOR_WHITE)
            screen.blit(datetime_text, (x + width - datetime_text.get_width() - 15, y + 15))

            time_text = FONT_SMALL.render(appt.appointment_time, True, (200, 220, 255))
            screen.blit(time_text, (x + width - time_text.get_width() - 15, y + 38))

    def draw_activity_section(self, screen, y):
        header_text = FONT_MEDIUM.render("Today's Activity", True, COLOR_BLACK)
        screen.blit(header_text, (20, y))

        ring_center = (SCREEN_WIDTH // 2, y + 100)
        draw_activity_ring(screen, ring_center, 50, RED, min(1.0, self.steps_today / self.steps_goal))
        draw_activity_ring(screen, ring_center, 38, GREEN, 0.85)
        draw_activity_ring(screen, ring_center, 26, BLUE, 0.60)

        labels_y = y + 170

        steps_progress = min(100, int((self.steps_today / self.steps_goal) * 100))
        steps_text = FONT_SMALL.render(f"Steps: {self.steps_today:,} / {self.steps_goal:,} ({steps_progress}%)", True, RED)
        screen.blit(steps_text, (SCREEN_WIDTH // 2 - steps_text.get_width() // 2, labels_y))

        exercise_text = FONT_SMALL.render("Exercise: 32 / 30 min (107%)", True, GREEN)
        screen.blit(exercise_text, (SCREEN_WIDTH // 2 - exercise_text.get_width() // 2, labels_y + 22))

        stand_text = FONT_SMALL.render("Stand: 8 / 12 hours (67%)", True, BLUE)
        screen.blit(stand_text, (SCREEN_WIDTH // 2 - stand_text.get_width() // 2, labels_y + 44))

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 20
            self.scroll_y = max(0, min(100, self.scroll_y))

        return None