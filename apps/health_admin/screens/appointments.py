import pygame
from datetime import datetime, timedelta
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database, Appointment

BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
ORANGE = (255, 149, 0)
PURPLE = (175, 82, 222)
PINK = (255, 45, 85)
TEAL = (90, 200, 250)
GREY = (142, 142, 147)
LIGHT_BG = (245, 245, 250)

FONT_LARGE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 12)
FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)

NAVBAR_HEIGHT = 85


class AppointmentsScreen:

    def __init__(self):
        self.db = Database()
        self.background_color = LIGHT_BG

        self.is_admin = False
        self.is_doctor = False
        self.current_doctor_id = None

        self.appointments = []
        self.selected_appointment = None

        self.mode = "list"

        self.filter_status = "all"
        self.filter_buttons = []

        self.scroll_y = 0
        self.max_scroll = 0

        self.fields = {
            "patient": "",
            "doctor": "",
            "date": "",
            "time": "",
            "notes": ""
        }
        self.active_field = None
        self.dropdown_open = None
        self.dropdown_y = 0

        self.patients = []
        self.doctors = []

        self.card_rects = []
        self.button_rects = {}

        pygame.key.set_repeat(400, 50)

    def load_appointments(self, doctor_id=None):
        if doctor_id is not None:
            self.is_admin = False
            self.is_doctor = True
            self.current_doctor_id = doctor_id
        else:
            self.is_admin = True
            self.is_doctor = False
            self.current_doctor_id = None

        if self.is_doctor and self.current_doctor_id:
            if self.filter_status == "all":
                self.appointments = self.db.get_appointments_by_doctor(self.current_doctor_id)
            else:
                self.appointments = self.db.get_appointments_by_doctor(self.current_doctor_id, self.filter_status)
        else:
            if self.filter_status == "all":
                self.appointments = self.db.get_all_appointments()
            else:
                self.appointments = self.db.get_all_appointments(self.filter_status)

        if self.is_admin:
            self.patients = self.db.get_all_patients()
            self.doctors = self.db.get_all_doctors()
        else:
            self.patients = self.db.get_patients_by_doctor(self.current_doctor_id)
            self.doctors = self.db.get_all_doctors()

    def reset_form(self):
        self.fields = {
            "patient": "",
            "doctor": "",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "09:00",
            "notes": ""
        }
        self.active_field = None
        self.dropdown_open = None

    def get_patient_options(self):
        return [p.name for p in self.patients]

    def get_doctor_options(self):
        return [f"{d.name} ({d.specialty})" for d in self.doctors]

    def get_time_options(self):
        times = []
        for hour in range(9, 18):
            times.append(f"{hour:02d}:00")
            times.append(f"{hour:02d}:30")
        return times

    def get_patient_id_by_name(self, name):
        for patient in self.patients:
            if patient.name == name:
                return patient.id
        return None

    def get_doctor_id_by_selection(self, selection):
        for doctor in self.doctors:
            if f"{doctor.name} ({doctor.specialty})" == selection:
                return doctor.id
        return None

    def get_doctor_name_by_id(self, doctor_id):
        for doctor in self.doctors:
            if doctor.id == doctor_id:
                return doctor.name
        return "Unknown"

    def save_appointment(self):
        if not self.is_admin:
            return False

        patient_id = self.get_patient_id_by_name(self.fields["patient"])
        doctor_id = self.get_doctor_id_by_selection(self.fields["doctor"])

        if not patient_id or not doctor_id or not self.fields["date"] or not self.fields["time"]:
            return False

        try:
            appt_date = datetime.strptime(self.fields["date"], "%Y-%m-%d")
        except ValueError:
            return False

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appt_date,
            appointment_time=self.fields["time"],
            status="scheduled",
            notes=self.fields["notes"]
        )

        self.db.add_appointment(appointment)
        self.mode = "list"
        self.reset_form()

        self.load_appointments()
        return True

    def update_appointment_status(self, appointment_id, new_status):
        self.db.update_appointment_status(appointment_id, new_status)

        if self.is_doctor:
            self.load_appointments(doctor_id=self.current_doctor_id)
        else:
            self.load_appointments()

    def delete_appointment(self, appointment_id):
        if not self.is_admin:
            return False

        self.db.delete_appointment(appointment_id)

        self.load_appointments()
        return True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if self.mode == "list":
                return self.handle_list_click(x, y)
            elif self.mode == "view":
                return self.handle_view_click(x, y)
            elif self.mode == "add":
                return self.handle_form_click(x, y)

        elif event.type == pygame.KEYDOWN:
            return self.handle_keydown(event)

        elif event.type == pygame.MOUSEWHEEL:
            if self.mode == "list":
                self.scroll_y -= event.y * 30
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))

        return None

    def handle_list_click(self, x, y):
        # Add button (admin only)
        if "add_btn" in self.button_rects:
            if self.button_rects["add_btn"].collidepoint(x, y):
                if self.is_admin:
                    self.mode = "add"
                    self.reset_form()
                    self.scroll_y = 0
                return None

        for filter_rect, filter_value in self.filter_buttons:
            if filter_rect.collidepoint(x, y):
                self.filter_status = filter_value
                if self.is_doctor:
                    self.load_appointments(doctor_id=self.current_doctor_id)
                else:
                    self.load_appointments()
                self.scroll_y = 0
                return None

        for card_rect, appointment in self.card_rects:
            if card_rect.collidepoint(x, y):
                self.selected_appointment = appointment
                self.mode = "view"
                self.scroll_y = 0
                return None

        return None

    def handle_view_click(self, x, y):
        if "back_btn" in self.button_rects:
            if self.button_rects["back_btn"].collidepoint(x, y):
                self.mode = "list"
                self.selected_appointment = None
                self.scroll_y = 0
                return None

        if "complete_btn" in self.button_rects:
            if self.button_rects["complete_btn"].collidepoint(x, y):
                self.update_appointment_status(self.selected_appointment.id, "completed")
                self.mode = "list"
                self.selected_appointment = None
                return None

        if "cancel_btn" in self.button_rects:
            if self.button_rects["cancel_btn"].collidepoint(x, y):
                self.update_appointment_status(self.selected_appointment.id, "cancelled")
                self.mode = "list"
                self.selected_appointment = None
                return None

        if "delete_btn" in self.button_rects:
            if self.button_rects["delete_btn"].collidepoint(x, y):
                if self.is_admin:
                    self.delete_appointment(self.selected_appointment.id)
                    self.mode = "list"
                    self.selected_appointment = None
                return None

        return None

    def handle_form_click(self, x, y):
        if "back_btn" in self.button_rects:
            if self.button_rects["back_btn"].collidepoint(x, y):
                self.mode = "list"
                self.reset_form()
                self.scroll_y = 0
                return None

        if "save_btn" in self.button_rects:
            if self.button_rects["save_btn"].collidepoint(x, y):
                self.save_appointment()
                return None

        if self.dropdown_open and "dropdown_options" in self.button_rects:
            for option_rect, option_value in self.button_rects["dropdown_options"]:
                if option_rect.collidepoint(x, y):
                    self.fields[self.dropdown_open] = option_value
                    self.dropdown_open = None
                    return None

        if self.dropdown_open:
            self.dropdown_open = None
            return None

        for field_name, rect in self.button_rects.items():
            if field_name.startswith("field_") and rect.collidepoint(x, y):
                actual_field = field_name.replace("field_", "")
                if actual_field in ["patient", "doctor", "time"]:
                    self.dropdown_open = actual_field
                    self.active_field = None
                else:
                    self.active_field = actual_field
                    self.dropdown_open = None
                return None

        self.active_field = None
        return None

    def handle_keydown(self, event):
        if self.mode == "add" and self.active_field:
            if event.key == pygame.K_BACKSPACE:
                self.fields[self.active_field] = self.fields[self.active_field][:-1]
            elif event.key == pygame.K_ESCAPE:
                self.active_field = None
            elif event.unicode and event.unicode.isprintable():
                if len(self.fields[self.active_field]) < 200:
                    self.fields[self.active_field] += event.unicode

        elif event.key == pygame.K_ESCAPE:
            if self.mode in ["add", "view"]:
                self.mode = "list"
                self.reset_form()
                self.selected_appointment = None
                self.scroll_y = 0

        return None

    def update(self):
        pass

    def draw(self, screen):
        screen.fill(self.background_color)

        self.button_rects = {}
        self.card_rects = []
        self.filter_buttons = []

        if self.mode == "list":
            self.draw_list(screen)
        elif self.mode == "view":
            self.draw_view(screen)
        elif self.mode == "add":
            self.draw_form(screen)

    def draw_list(self, screen):
        if self.is_admin:
            title_text = "All Appointments"
        else:
            title_text = "My Schedule"

        title = FONT_LARGE.render(title_text, True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        badge_x = 20 + title.get_width() + 10
        badge_y = 60
        if self.is_admin:
            pygame.draw.rect(screen, PURPLE, (badge_x, badge_y, 55, 20), border_radius=10)
            badge_text = FONT_TINY.render("ADMIN", True, COLOR_WHITE)
        else:
            pygame.draw.rect(screen, TEAL, (badge_x, badge_y, 60, 20), border_radius=10)
            badge_text = FONT_TINY.render("DOCTOR", True, COLOR_WHITE)
        screen.blit(badge_text, (badge_x + 8, badge_y + 4))

        # Add button (admin only)
        if self.is_admin:
            add_btn = pygame.Rect(SCREEN_WIDTH - 50, 55, 35, 35)
            pygame.draw.rect(screen, BLUE, add_btn, border_radius=10)
            plus_font = pygame.font.SysFont("Arial", 24, bold=True)
            plus_text = plus_font.render("+", True, COLOR_WHITE)
            screen.blit(plus_text, (add_btn.x + 10, add_btn.y + 3))
            self.button_rects["add_btn"] = add_btn

        filter_y = 100
        filters = [
            ("All", "all"),
            ("Scheduled", "scheduled"),
            ("Completed", "completed"),
            ("Cancelled", "cancelled")
        ]

        filter_x = 15
        for label, value in filters:
            is_active = self.filter_status == value
            width = len(label) * 9 + 20
            btn_rect = pygame.Rect(filter_x, filter_y, width, 32)

            if is_active:
                pygame.draw.rect(screen, BLUE, btn_rect, border_radius=16)
                text_color = COLOR_WHITE
            else:
                pygame.draw.rect(screen, COLOR_WHITE, btn_rect, border_radius=16)
                pygame.draw.rect(screen, (220, 220, 220), btn_rect, 1, border_radius=16)
                text_color = COLOR_BLACK

            label_surface = FONT_SMALL.render(label, True, text_color)
            screen.blit(label_surface, (filter_x + (width - label_surface.get_width()) // 2,
                                        filter_y + 7))

            self.filter_buttons.append((btn_rect, value))
            filter_x += width + 8

        list_y = 150 - self.scroll_y
        content_height = 0

        if not self.appointments:
            empty_y = 250
            if self.is_doctor:
                if self.filter_status == "all":
                    empty_text = FONT_BODY.render("No appointments scheduled", True, GREY)
                else:
                    empty_text = FONT_BODY.render(f"No {self.filter_status} appointments", True, GREY)
                hint_text = FONT_SMALL.render("Your schedule is clear! 🎉", True, GREY)
            else:
                empty_text = FONT_BODY.render("No appointments found", True, GREY)
                hint_text = FONT_SMALL.render("Tap + to schedule one", True, BLUE)

            screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, empty_y))
            screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, empty_y + 30))
        else:
            for i, appointment in enumerate(self.appointments):
                card_y = list_y + (i * 100)
                if 130 < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 20:
                    card_rect = self.draw_appointment_card(screen, appointment, 15, card_y)
                    self.card_rects.append((card_rect, appointment))
                content_height = (i + 1) * 100

        self.max_scroll = max(0, content_height - (SCREEN_HEIGHT - NAVBAR_HEIGHT - 180))

    def draw_appointment_card(self, screen, appointment, x, y):
        width = SCREEN_WIDTH - 30
        height = 90

        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

        status_colors = {
            "scheduled": BLUE,
            "completed": GREEN,
            "cancelled": RED
        }
        status_color = status_colors.get(appointment.status, GREY)

        status_bar = pygame.Rect(x, y, 5, height)
        pygame.draw.rect(screen, status_color, status_bar,
                        border_top_left_radius=15, border_bottom_left_radius=15)

        if appointment.appointment_date:
            date_str = appointment.appointment_date.strftime("%b %d")
            day_str = appointment.appointment_date.strftime("%a")
        else:
            date_str = "N/A"
            day_str = ""

        date_box_x = x + 20
        date_box_y = y + 15
        pygame.draw.rect(screen, (240, 245, 255), (date_box_x, date_box_y, 50, 55), border_radius=10)

        day_text = FONT_TINY.render(day_str, True, BLUE)
        screen.blit(day_text, (date_box_x + 25 - day_text.get_width() // 2, date_box_y + 8))

        date_text = FONT_MEDIUM.render(date_str.split()[1] if " " in date_str else date_str, True, BLUE)
        screen.blit(date_text, (date_box_x + 25 - date_text.get_width() // 2, date_box_y + 25))

        month_text = FONT_TINY.render(date_str.split()[0] if " " in date_str else "", True, BLUE)
        screen.blit(month_text, (date_box_x + 25 - month_text.get_width() // 2, date_box_y + 45))

        patient_name = getattr(appointment, 'patient_name', 'Unknown Patient')
        patient_text = FONT_MEDIUM.render(patient_name, True, COLOR_BLACK)
        screen.blit(patient_text, (x + 85, y + 15))

        # Doctor name (only show for admin view)
        if self.is_admin:
            doctor_name = getattr(appointment, 'doctor_name', 'Unknown Doctor')
            doctor_text = FONT_SMALL.render(f"Dr. {doctor_name}", True, GREY)
            screen.blit(doctor_text, (x + 85, y + 40))

            # Time
            time_text = FONT_SMALL.render(appointment.appointment_time, True, BLUE)
            screen.blit(time_text, (x + 85, y + 62))
        else:
            # Doctor view - show notes or time on second line
            notes = appointment.notes if appointment.notes else "General consultation"
            if len(notes) > 25:
                notes = notes[:22] + "..."
            notes_text = FONT_SMALL.render(notes, True, GREY)
            screen.blit(notes_text, (x + 85, y + 40))

            # Time
            time_text = FONT_SMALL.render(appointment.appointment_time, True, BLUE)
            screen.blit(time_text, (x + 85, y + 62))

        # Status badge
        status_badge_x = x + width - 80
        status_badge_y = y + 35
        badge_width = 70
        badge_height = 22

        pygame.draw.rect(screen, (*status_color, 30), (status_badge_x, status_badge_y, badge_width, badge_height),
                        border_radius=11)
        status_text = FONT_TINY.render(appointment.status.capitalize(), True, status_color)
        screen.blit(status_text, (status_badge_x + (badge_width - status_text.get_width()) // 2,
                                  status_badge_y + 4))

        return card_rect

    def draw_view(self, screen):
        back_btn = self.draw_back_button(screen, 15, 55)
        self.button_rects["back_btn"] = back_btn

        title = FONT_MEDIUM.render("Appointment Details", True, COLOR_BLACK)
        screen.blit(title, (70, 60))

        if not self.selected_appointment:
            return

        appt = self.selected_appointment

        card_y = 110
        card_height = 200
        card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, card_height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=20)

        status_colors = {
            "scheduled": BLUE,
            "completed": GREEN,
            "cancelled": RED
        }
        status_color = status_colors.get(appt.status, GREY)
        pygame.draw.rect(screen, status_color, (15, card_y, 6, card_height),
                        border_top_left_radius=20, border_bottom_left_radius=20)

        if appt.appointment_date:
            date_str = appt.appointment_date.strftime("%A, %B %d, %Y")
        else:
            date_str = "Date not set"

        date_text = FONT_MEDIUM.render(date_str, True, COLOR_BLACK)
        screen.blit(date_text, (35, card_y + 20))

        time_text = FONT_LARGE.render(appt.appointment_time or "N/A", True, status_color)
        screen.blit(time_text, (35, card_y + 50))

        patient_label = FONT_TINY.render("PATIENT", True, GREY)
        screen.blit(patient_label, (35, card_y + 100))

        patient_name = getattr(appt, 'patient_name', 'Unknown')
        patient_text = FONT_BODY.render(patient_name, True, COLOR_BLACK)
        screen.blit(patient_text, (35, card_y + 118))

        doctor_label = FONT_TINY.render("DOCTOR", True, GREY)
        screen.blit(doctor_label, (35, card_y + 150))

        doctor_name = getattr(appt, 'doctor_name', 'Unknown')
        doctor_spec = getattr(appt, 'doctor_specialty', '')
        doctor_text = FONT_BODY.render(f"Dr. {doctor_name}", True, COLOR_BLACK)
        screen.blit(doctor_text, (35, card_y + 168))

        if doctor_spec:
            spec_text = FONT_TINY.render(doctor_spec, True, BLUE)
            screen.blit(spec_text, (35 + doctor_text.get_width() + 10, card_y + 172))

        badge_x = SCREEN_WIDTH - 100
        badge_y = card_y + 20
        pygame.draw.rect(screen, status_color, (badge_x, badge_y, 70, 26), border_radius=13)
        status_text = FONT_SMALL.render(appt.status.capitalize(), True, COLOR_WHITE)
        screen.blit(status_text, (badge_x + 35 - status_text.get_width() // 2, badge_y + 5))

        notes_y = card_y + card_height + 20
        notes_height = 100
        notes_rect = pygame.Rect(15, notes_y, SCREEN_WIDTH - 30, notes_height)
        pygame.draw.rect(screen, COLOR_WHITE, notes_rect, border_radius=15)

        notes_label = FONT_TINY.render("NOTES", True, GREY)
        screen.blit(notes_label, (30, notes_y + 15))

        notes_content = appt.notes if appt.notes else "No notes added"
        notes_text = FONT_BODY.render(notes_content, True, COLOR_BLACK)
        screen.blit(notes_text, (30, notes_y + 40))

        buttons_y = notes_y + notes_height + 25

        if appt.status == "scheduled":
            # Both admin and doctor can complete/cancel scheduled appointments
            complete_btn = pygame.Rect(15, buttons_y, (SCREEN_WIDTH - 40) // 2, 50)
            pygame.draw.rect(screen, GREEN, complete_btn, border_radius=12)
            complete_text = FONT_BUTTON.render("Complete", True, COLOR_WHITE)
            screen.blit(complete_text, (complete_btn.x + complete_btn.width // 2 - complete_text.get_width() // 2,
                                        complete_btn.y + 13))
            self.button_rects["complete_btn"] = complete_btn

            cancel_btn = pygame.Rect(SCREEN_WIDTH // 2 + 5, buttons_y, (SCREEN_WIDTH - 40) // 2, 50)
            pygame.draw.rect(screen, COLOR_WHITE, cancel_btn, border_radius=12)
            pygame.draw.rect(screen, ORANGE, cancel_btn, 2, border_radius=12)
            cancel_text = FONT_BUTTON.render("Cancel", True, ORANGE)
            screen.blit(cancel_text, (cancel_btn.x + cancel_btn.width // 2 - cancel_text.get_width() // 2,
                                      cancel_btn.y + 13))
            self.button_rects["cancel_btn"] = cancel_btn

        else:
            if self.is_admin:
                delete_btn = pygame.Rect(15, buttons_y, SCREEN_WIDTH - 30, 50)
                pygame.draw.rect(screen, COLOR_WHITE, delete_btn, border_radius=12)
                pygame.draw.rect(screen, RED, delete_btn, 2, border_radius=12)
                delete_text = FONT_BUTTON.render("Delete Appointment", True, RED)
                screen.blit(delete_text, (delete_btn.x + delete_btn.width // 2 - delete_text.get_width() // 2,
                                          delete_btn.y + 13))
                self.button_rects["delete_btn"] = delete_btn
            else:
                info_text = FONT_BODY.render(f"This appointment is {appt.status}", True, GREY)
                screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, buttons_y + 15))

    def draw_form(self, screen):
        back_btn = self.draw_back_button(screen, 15, 55)
        self.button_rects["back_btn"] = back_btn

        title = FONT_MEDIUM.render("New Appointment", True, COLOR_BLACK)
        screen.blit(title, (70, 60))

        badge_x = 70 + title.get_width() + 10
        badge_y = 63
        pygame.draw.rect(screen, PURPLE, (badge_x, badge_y, 55, 20), border_radius=10)
        badge_text = FONT_TINY.render("ADMIN", True, COLOR_WHITE)
        screen.blit(badge_text, (badge_x + 10, badge_y + 4))

        form_y = 105
        form_rect = pygame.Rect(15, form_y, SCREEN_WIDTH - 30, 450)
        pygame.draw.rect(screen, COLOR_WHITE, form_rect, border_radius=20)

        current_y = form_y + 20
        field_width = SCREEN_WIDTH - 70

        current_y = self.draw_dropdown_field(screen, "patient", "Select Patient", 35, current_y, field_width, self.get_patient_options())

        current_y = self.draw_dropdown_field(screen, "doctor", "Select Doctor", 35, current_y, field_width, self.get_doctor_options())

        current_y = self.draw_form_field(screen, "date", "Date (YYYY-MM-DD)", 35, current_y, field_width)

        current_y = self.draw_dropdown_field(screen, "time", "Select Time", 35, current_y, field_width, self.get_time_options())

        current_y = self.draw_form_field(screen, "notes", "Notes (optional)", 35, current_y, field_width)

        save_y = form_y + 395
        save_btn = pygame.Rect(35, save_y, field_width, 50)
        can_save = self.fields["patient"] and self.fields["doctor"] and self.fields["date"] and self.fields["time"]
        btn_color = BLUE if can_save else GREY
        pygame.draw.rect(screen, btn_color, save_btn, border_radius=12)
        save_text = FONT_BUTTON.render("Schedule Appointment", True, COLOR_WHITE)
        screen.blit(save_text, (save_btn.x + save_btn.width // 2 - save_text.get_width() // 2,
                                save_btn.y + 13))
        self.button_rects["save_btn"] = save_btn

        if self.dropdown_open:
            if self.dropdown_open == "patient":
                options = self.get_patient_options()[:5]
            elif self.dropdown_open == "doctor":
                options = self.get_doctor_options()[:4]
            elif self.dropdown_open == "time":
                options = self.get_time_options()[:6]
            else:
                options = []

            if options:
                self.draw_dropdown_options(screen, 35, self.dropdown_y + 52, field_width, options)

    def draw_form_field(self, screen, field_name, placeholder, x, y, width):
        field_height = 50

        border_color = BLUE if self.active_field == field_name else (220, 220, 220)

        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, LIGHT_BG, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)
        self.button_rects[f"field_{field_name}"] = input_rect

        value = self.fields.get(field_name, "")
        if value:
            text_surface = FONT_BODY.render(value, True, COLOR_BLACK)
            screen.blit(text_surface, (x + 15, y + (field_height - text_surface.get_height()) // 2))

            if self.active_field == field_name:
                cursor_x = x + 15 + text_surface.get_width() + 2
                pygame.draw.line(screen, COLOR_BLACK, (cursor_x, y + 12), (cursor_x, y + field_height - 12), 2)
        else:
            if self.active_field == field_name:
                pygame.draw.line(screen, COLOR_BLACK, (x + 15, y + 12), (x + 15, y + field_height - 12), 2)
            else:
                placeholder_surface = FONT_BODY.render(placeholder, True, GREY)
                screen.blit(placeholder_surface, (x + 15, y + (field_height - placeholder_surface.get_height()) // 2))

        return y + field_height + 12

    def draw_dropdown_field(self, screen, field_name, placeholder, x, y, width, options):
        field_height = 50

        self.dropdown_y = y if self.dropdown_open == field_name else self.dropdown_y

        border_color = BLUE if self.dropdown_open == field_name else (220, 220, 220)

        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, LIGHT_BG, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)
        self.button_rects[f"field_{field_name}"] = input_rect

        value = self.fields.get(field_name, "")
        if value:
            display_value = value if len(value) <= 30 else value[:27] + "..."
            text_surface = FONT_BODY.render(display_value, True, COLOR_BLACK)
        else:
            text_surface = FONT_BODY.render(placeholder, True, GREY)
        screen.blit(text_surface, (x + 15, y + (field_height - text_surface.get_height()) // 2))

        arrow = "▼" if self.dropdown_open != field_name else "▲"
        arrow_surface = FONT_BODY.render(arrow, True, GREY)
        screen.blit(arrow_surface, (x + width - 30, y + (field_height - arrow_surface.get_height()) // 2))

        return y + field_height + 12

    def draw_dropdown_options(self, screen, x, y, width, options):
        option_height = 44
        dropdown_height = len(options) * option_height
        pygame.draw.rect(screen, (200, 200, 200), (x + 3, y + 3, width, dropdown_height), border_radius=12)

        pygame.draw.rect(screen, COLOR_WHITE, (x, y, width, dropdown_height), border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), (x, y, width, dropdown_height), 1, border_radius=12)

        option_rects = []
        current_value = self.fields.get(self.dropdown_open, "")

        for i, option in enumerate(options):
            option_y = y + (i * option_height)
            option_rect = pygame.Rect(x, option_y, width, option_height)
            option_rects.append((option_rect, option))

            if option == current_value:
                highlight = pygame.Surface((width - 8, option_height - 8), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (0, 122, 255, 30), (0, 0, width - 8, option_height - 8), border_radius=8)
                screen.blit(highlight, (x + 4, option_y + 4))

            display_option = option if len(option) <= 35 else option[:32] + "..."
            option_surface = FONT_SMALL.render(display_option, True, COLOR_BLACK)
            screen.blit(option_surface, (x + 15, option_y + (option_height - option_surface.get_height()) // 2))

            if i < len(options) - 1:
                pygame.draw.line(screen, (240, 240, 240), (x + 15, option_y + option_height),
                               (x + width - 15, option_y + option_height), 1)

        self.button_rects["dropdown_options"] = option_rects

    def draw_back_button(self, screen, x, y):
        back_rect = pygame.Rect(x, y, 45, 35)
        pygame.draw.rect(screen, (240, 240, 245), back_rect, border_radius=10)

        arrow_x = x + 15
        arrow_y = y + 17
        pygame.draw.line(screen, BLUE, (arrow_x + 8, arrow_y - 6), (arrow_x, arrow_y), 2)
        pygame.draw.line(screen, BLUE, (arrow_x, arrow_y), (arrow_x + 8, arrow_y + 6), 2)

        return back_rect