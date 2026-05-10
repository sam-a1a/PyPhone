import pygame
from datetime import datetime, timedelta
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
GREEN = (52, 199, 89)
RED = (255, 59, 48)
ORANGE = (255, 149, 0)

FONT_LARGE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)


class HistoryScreen:

    def __init__(self):
        self.background_color = (245, 245, 250)
        self.db = Database()
        self.current_patient_id = 1
        self.appointments = []
        self.scroll_y = 0
        self.selected_tab = "upcoming"

        self.state = "list"
        self.selected_appointment = None
        self.edit_date = None
        self.edit_time = None
        self.booked_slots = []

        self.load_appointments()

    def load_appointments(self):
        self.appointments = self.db.get_appointments_by_patient(self.current_patient_id)

    def get_filtered_appointments(self):
        if self.selected_tab == "upcoming":
            return [a for a in self.appointments if a.status == 'scheduled']
        elif self.selected_tab == "past":
            return [a for a in self.appointments if a.status in ['completed', 'cancelled']]
        else:
            return self.appointments

    def load_booked_slots_for_edit(self):
        if self.selected_appointment and self.edit_date:
            all_booked = self.db.get_booked_slots(
                self.selected_appointment.doctor_id,
                self.edit_date
            )
            if (self.selected_appointment.appointment_date and
                self.edit_date.strftime("%Y-%m-%d") == self.selected_appointment.appointment_date.strftime("%Y-%m-%d")):
                self.booked_slots = [t for t in all_booked if t != self.selected_appointment.appointment_time]
            else:
                self.booked_slots = all_booked
        else:
            self.booked_slots = []

    def draw(self, screen):
        screen.fill(self.background_color)

        if self.state == "list":
            self.draw_list(screen)
        elif self.state == "edit":
            self.draw_edit(screen)
        elif self.state == "delete_confirm":
            self.draw_delete_confirm(screen)

    def draw_list(self, screen):
        title = FONT_LARGE.render("My Appointments", True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        self.draw_tabs(screen, 20, 100)

        filtered = self.get_filtered_appointments()
        count_text = FONT_SMALL.render(f"{len(filtered)} appointments", True, GREY)
        screen.blit(count_text, (20, 150))

        list_y = 180

        if not filtered:
            empty_text = FONT_BODY.render("No appointments found", True, GREY)
            screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, list_y + 50))

            if self.selected_tab == "upcoming":
                suggest_text = FONT_SMALL.render("Book a doctor from the Book tab", True, BLUE)
                screen.blit(suggest_text, (SCREEN_WIDTH // 2 - suggest_text.get_width() // 2, list_y + 80))
        else:
            self.appointment_cards = []
            for i, appt in enumerate(filtered):
                card_y = list_y + (i * 130) - self.scroll_y
                if 160 < card_y < SCREEN_HEIGHT - 120:
                    self.draw_appointment_card(screen, appt, 20, card_y)
                    self.appointment_cards.append((pygame.Rect(20, card_y, SCREEN_WIDTH - 40, 120), appt))

    def draw_tabs(self, screen, x, y):
        tabs = [
            ("upcoming", "Upcoming"),
            ("past", "Past"),
            ("all", "All")
        ]

        tab_width = (SCREEN_WIDTH - 60) // 3
        self.tab_buttons = []

        for i, (key, label) in enumerate(tabs):
            tab_x = x + (i * (tab_width + 10))
            is_selected = self.selected_tab == key

            btn_color = BLUE if is_selected else COLOR_WHITE
            text_color = COLOR_WHITE if is_selected else COLOR_BLACK

            btn_rect = pygame.Rect(tab_x, y, tab_width, 35)
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
            if not is_selected:
                pygame.draw.rect(screen, (220, 220, 220), btn_rect, 1, border_radius=10)

            if key == "upcoming":
                count = len([a for a in self.appointments if a.status == 'scheduled'])
            elif key == "past":
                count = len([a for a in self.appointments if a.status in ['completed', 'cancelled']])
            else:
                count = len(self.appointments)

            label_with_count = f"{label} ({count})"
            label_text = FONT_SMALL.render(label_with_count, True, text_color)
            screen.blit(label_text, (tab_x + tab_width // 2 - label_text.get_width() // 2, y + 8))

            self.tab_buttons.append((btn_rect, key))

    def draw_appointment_card(self, screen, appt, x, y):
        width = SCREEN_WIDTH - 40
        height = 120

        pygame.draw.rect(screen, COLOR_WHITE, (x, y, width, height), border_radius=12)
        pygame.draw.rect(screen, (230, 230, 230), (x, y, width, height), 1, border_radius=12)

        status_colors = {
            'scheduled': BLUE,
            'completed': GREEN,
            'cancelled': RED
        }
        status_color = status_colors.get(appt.status, GREY)
        pygame.draw.rect(screen, status_color, (x + 10, y + 15, 4, height - 30), border_radius=2)

        doctor_text = FONT_MEDIUM.render(f"Dr. {appt.doctor_name}", True, COLOR_BLACK)
        screen.blit(doctor_text, (x + 25, y + 15))

        spec_text = FONT_SMALL.render(appt.doctor_specialty, True, GREY)
        screen.blit(spec_text, (x + 25, y + 40))

        if appt.appointment_date:
            date_str = appt.appointment_date.strftime("%B %d, %Y")
            datetime_text = FONT_BODY.render(f"📅 {date_str} at {appt.appointment_time}", True, COLOR_BLACK)
            screen.blit(datetime_text, (x + 25, y + 65))

        status_text = FONT_SMALL.render(appt.status.upper(), True, COLOR_WHITE)
        badge_width = status_text.get_width() + 16
        badge_x = x + width - badge_width - 15
        pygame.draw.rect(screen, status_color, (badge_x, y + 15, badge_width, 24), border_radius=12)
        screen.blit(status_text, (badge_x + 8, y + 18))

        if appt.status == 'scheduled':
            btn_y = y + height - 35

            self.edit_btn_rect = pygame.Rect(x + width - 140, btn_y, 60, 28)
            pygame.draw.rect(screen, BLUE, self.edit_btn_rect, border_radius=8)
            edit_text = FONT_SMALL.render("Edit", True, COLOR_WHITE)
            screen.blit(edit_text, (self.edit_btn_rect.x + 18, btn_y + 5))

            self.delete_btn_rect = pygame.Rect(x + width - 70, btn_y, 60, 28)
            pygame.draw.rect(screen, RED, self.delete_btn_rect, border_radius=8)
            delete_text = FONT_SMALL.render("Delete", True, COLOR_WHITE)
            screen.blit(delete_text, (self.delete_btn_rect.x + 10, btn_y + 5))

    def draw_edit(self, screen):
        if not self.selected_appointment:
            return

        back_text = FONT_BODY.render("< Cancel", True, BLUE)
        screen.blit(back_text, (20, 55))

        title = FONT_LARGE.render("Edit Appointment", True, COLOR_BLACK)
        screen.blit(title, (20, 90))

        doctor_text = FONT_BODY.render(f"Doctor: {self.selected_appointment.doctor_name}", True, GREY)
        screen.blit(doctor_text, (20, 130))

        current_text = FONT_SMALL.render("Current:", True, GREY)
        screen.blit(current_text, (20, 160))

        if self.selected_appointment.appointment_date:
            current_datetime = FONT_BODY.render(
                f"{self.selected_appointment.appointment_date.strftime('%B %d, %Y')} at {self.selected_appointment.appointment_time}",
                True, COLOR_BLACK
            )
            screen.blit(current_datetime, (80, 158))

        date_y = 200
        date_label = FONT_SMALL.render("New Date:", True, GREY)
        screen.blit(date_label, (20, date_y))

        self.date_buttons = []
        date_y += 25
        for i in range(7):
            date = datetime.now() + timedelta(days=i)
            btn_x = 20 + (i * 55)

            is_selected = self.edit_date and self.edit_date.date() == date.date()
            btn_color = BLUE if is_selected else COLOR_WHITE
            text_color = COLOR_WHITE if is_selected else COLOR_BLACK

            btn_rect = pygame.Rect(btn_x, date_y, 50, 65)
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
            if not is_selected:
                pygame.draw.rect(screen, (220, 220, 220), btn_rect, 1, border_radius=10)

            day_text = FONT_SMALL.render(date.strftime("%a"), True, text_color if is_selected else GREY)
            screen.blit(day_text, (btn_x + 25 - day_text.get_width() // 2, date_y + 8))

            num_text = FONT_MEDIUM.render(str(date.day), True, text_color)
            screen.blit(num_text, (btn_x + 25 - num_text.get_width() // 2, date_y + 30))

            self.date_buttons.append((btn_rect, date))

        time_y = date_y + 90
        times_label = FONT_SMALL.render("New Time:", True, GREY)
        screen.blit(times_label, (20, time_y))

        time_slots = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]
        self.time_buttons = []

        time_y += 25
        for i, time in enumerate(time_slots):
            row = i // 4
            col = i % 4
            btn_width = (SCREEN_WIDTH - 70) // 4
            btn_x = 20 + (col * (btn_width + 10))
            btn_y = time_y + (row * 50)

            is_booked = time in self.booked_slots
            is_selected = self.edit_time == time

            if is_booked:
                btn_color = (240, 240, 240)
                text_color = (180, 180, 180)
            elif is_selected:
                btn_color = BLUE
                text_color = COLOR_WHITE
            else:
                btn_color = COLOR_WHITE
                text_color = COLOR_BLACK

            btn_rect = pygame.Rect(btn_x, btn_y, btn_width, 40)
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)

            if not is_selected and not is_booked:
                pygame.draw.rect(screen, (220, 220, 220), btn_rect, 1, border_radius=10)

            time_text = FONT_BODY.render(time, True, text_color)
            screen.blit(time_text, (btn_x + btn_width // 2 - time_text.get_width() // 2, btn_y + 10))

            if not is_booked:
                self.time_buttons.append((btn_rect, time))

        if self.edit_date and self.edit_time:
            self.save_button_rect = pygame.Rect(20, 520, SCREEN_WIDTH - 40, 50)
            pygame.draw.rect(screen, GREEN, self.save_button_rect, border_radius=12)
            save_text = FONT_MEDIUM.render("Save Changes", True, COLOR_WHITE)
            screen.blit(save_text, (SCREEN_WIDTH // 2 - save_text.get_width() // 2, 533))

    def draw_delete_confirm(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        dialog_width = SCREEN_WIDTH - 60
        dialog_height = 220
        dialog_x = 30
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2

        pygame.draw.rect(screen, COLOR_WHITE, (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=20)

        warning_y = dialog_y + 30
        pygame.draw.circle(screen, RED, (SCREEN_WIDTH // 2, warning_y + 20), 25)
        warning_text = FONT_LARGE.render("!", True, COLOR_WHITE)
        screen.blit(warning_text, (SCREEN_WIDTH // 2 - warning_text.get_width() // 2, warning_y + 5))

        title = FONT_MEDIUM.render("Delete Appointment?", True, COLOR_BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, dialog_y + 85))

        msg = FONT_SMALL.render("This action cannot be undone.", True, GREY)
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, dialog_y + 115))

        btn_y = dialog_y + 155
        btn_width = (dialog_width - 30) // 2

        self.cancel_delete_rect = pygame.Rect(dialog_x + 10, btn_y, btn_width, 45)
        pygame.draw.rect(screen, (220, 220, 220), self.cancel_delete_rect, border_radius=10)
        cancel_text = FONT_BODY.render("Cancel", True, COLOR_BLACK)
        screen.blit(cancel_text, (self.cancel_delete_rect.centerx - cancel_text.get_width() // 2, btn_y + 12))

        self.confirm_delete_rect = pygame.Rect(dialog_x + btn_width + 20, btn_y, btn_width, 45)
        pygame.draw.rect(screen, RED, self.confirm_delete_rect, border_radius=10)
        delete_text = FONT_BODY.render("Delete", True, COLOR_WHITE)
        screen.blit(delete_text, (self.confirm_delete_rect.centerx - delete_text.get_width() // 2, btn_y + 12))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if self.state == "list":
                if hasattr(self, 'tab_buttons'):
                    for btn_rect, tab_key in self.tab_buttons:
                        if btn_rect.collidepoint(x, y):
                            self.selected_tab = tab_key
                            self.scroll_y = 0
                            return None

                if hasattr(self, 'appointment_cards'):
                    for card_rect, appt in self.appointment_cards:
                        if appt.status == 'scheduled':
                            edit_x = card_rect.right - 140
                            edit_y = card_rect.bottom - 35
                            edit_rect = pygame.Rect(edit_x, edit_y, 60, 28)
                            if edit_rect.collidepoint(x, y):
                                self.selected_appointment = appt
                                self.edit_date = appt.appointment_date
                                self.edit_time = appt.appointment_time
                                self.load_booked_slots_for_edit()
                                self.state = "edit"
                                return None

                            delete_x = card_rect.right - 70
                            delete_y = card_rect.bottom - 35
                            delete_rect = pygame.Rect(delete_x, delete_y, 60, 28)
                            if delete_rect.collidepoint(x, y):
                                self.selected_appointment = appt
                                self.state = "delete_confirm"
                                return None

            elif self.state == "edit":
                if y < 90 and x < 100:
                    self.state = "list"
                    self.selected_appointment = None
                    self.edit_date = None
                    self.edit_time = None
                    return None

                if hasattr(self, 'date_buttons'):
                    for btn_rect, date in self.date_buttons:
                        if btn_rect.collidepoint(x, y):
                            self.edit_date = date
                            self.edit_time = None
                            self.load_booked_slots_for_edit()
                            return None

                if hasattr(self, 'time_buttons'):
                    for btn_rect, time in self.time_buttons:
                        if btn_rect.collidepoint(x, y):
                            self.edit_time = time
                            return None

                if hasattr(self, 'save_button_rect') and self.save_button_rect.collidepoint(x, y):
                    self.save_changes()
                    return None

            elif self.state == "delete_confirm":
                if hasattr(self, 'cancel_delete_rect') and self.cancel_delete_rect.collidepoint(x, y):
                    self.state = "list"
                    self.selected_appointment = None
                    return None

                if hasattr(self, 'confirm_delete_rect') and self.confirm_delete_rect.collidepoint(x, y):
                    self.delete_appointment()
                    return None

        elif event.type == pygame.MOUSEWHEEL:
            if self.state == "list":
                self.scroll_y -= event.y * 30
                self.scroll_y = max(0, self.scroll_y)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state != "list":
                    self.state = "list"
                    self.selected_appointment = None
                    self.edit_date = None
                    self.edit_time = None

        return None

    def save_changes(self):
        if self.selected_appointment and self.edit_date and self.edit_time:
            self.selected_appointment.appointment_date = self.edit_date
            self.selected_appointment.appointment_time = self.edit_time
            success = self.db.update_appointment(self.selected_appointment)
            if success:
                self.load_appointments()
            self.state = "list"
            self.selected_appointment = None
            self.edit_date = None
            self.edit_time = None

    def delete_appointment(self):
        if self.selected_appointment:
            success = self.db.delete_appointment(self.selected_appointment.id)
            if success:
                self.load_appointments()
            self.state = "list"
            self.selected_appointment = None