import pygame
from datetime import datetime, timedelta
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database
from apps.shared.models import SPECIALTIES, Appointment

BLUE = (0, 122, 255)
GREY = (142, 142, 147)
GREEN = (52, 199, 89)
LIGHT_GREY = (245, 245, 250)
RED = (255, 59, 48)

FONT_LARGE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)


class BookScreen:

    def __init__(self):
        self.background_color = (245, 245, 250)
        self.db = Database()
        self.current_patient_id = 1

        self.state = "list"
        self.selected_specialty = None
        self.selected_doctor = None
        self.selected_date = None
        self.selected_time = None
        self.doctors = []
        self.scroll_y = 0

        self.search_text = ""
        self.search_active = False

        self.booked_slots = []

        pygame.key.set_repeat(400, 50)

        self.load_doctors()

    def load_doctors(self):
        if self.search_text:
            self.doctors = self.db.search_doctors(self.search_text)
        elif self.selected_specialty:
            self.doctors = self.db.get_doctors_by_specialty(self.selected_specialty)
        else:
            self.doctors = self.db.get_all_doctors()

    def load_booked_slots(self):
        if self.selected_doctor and self.selected_date:
            self.booked_slots = self.db.get_booked_slots(
                self.selected_doctor.id,
                self.selected_date
            )
        else:
            self.booked_slots = []

    def draw(self, screen):
        screen.fill(self.background_color)

        if self.state == "list":
            self.draw_doctor_list(screen)
        elif self.state == "doctor_detail":
            self.draw_doctor_detail(screen)
        elif self.state == "time_select":
            self.draw_time_select(screen)
        elif self.state == "confirm":
            self.draw_confirmation(screen)

    def draw_doctor_list(self, screen):
        title = FONT_LARGE.render("Find a Doctor", True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        search_y = 95
        self.search_rect = pygame.Rect(20, search_y, SCREEN_WIDTH - 40, 45)
        border_color = BLUE if self.search_active else (220, 220, 220)
        pygame.draw.rect(screen, COLOR_WHITE, self.search_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, self.search_rect, 2, border_radius=10)

        search_icon = FONT_BODY.render("🔍", True, GREY)
        screen.blit(search_icon, (30, search_y + 10))

        if self.search_text:
            search_display = FONT_BODY.render(self.search_text, True, COLOR_BLACK)
            screen.blit(search_display, (60, search_y + 12))
            if self.search_active:
                cursor_x = 60 + search_display.get_width() + 2
                pygame.draw.line(screen, COLOR_BLACK, (cursor_x, search_y + 10), (cursor_x, search_y + 35), 2)
        else:
            if self.search_active:
                pygame.draw.line(screen, COLOR_BLACK, (60, search_y + 10), (60, search_y + 35), 2)
            else:
                placeholder = FONT_BODY.render("Search doctors by name...", True, GREY)
                screen.blit(placeholder, (60, search_y + 12))

        filter_y = 155
        filter_text = FONT_SMALL.render("Filter by specialty:", True, GREY)
        screen.blit(filter_text, (20, filter_y))

        chip_y = filter_y + 25
        chip_x = 20
        specialties_to_show = ["All"] + SPECIALTIES[:4]

        self.specialty_chips = []
        for spec in specialties_to_show:
            is_selected = (spec == "All" and not self.selected_specialty) or (spec == self.selected_specialty)
            chip_color = BLUE if is_selected else (220, 220, 220)
            text_color = COLOR_WHITE if is_selected else COLOR_BLACK

            chip_text = FONT_SMALL.render(spec, True, text_color)
            chip_width = chip_text.get_width() + 20

            if chip_x + chip_width > SCREEN_WIDTH - 20:
                chip_y += 35
                chip_x = 20

            chip_rect = pygame.Rect(chip_x, chip_y, chip_width, 28)
            pygame.draw.rect(screen, chip_color, chip_rect, border_radius=14)
            screen.blit(chip_text, (chip_x + 10, chip_y + 5))

            self.specialty_chips.append((chip_rect, spec))
            chip_x += chip_width + 10

        count_y = chip_y + 45
        count_text = FONT_SMALL.render(f"{len(self.doctors)} doctors found", True, GREY)
        screen.blit(count_text, (20, count_y))

        list_y = count_y + 30
        self.doctor_cards = []

        if not self.doctors:
            no_docs = FONT_BODY.render("No doctors found", True, GREY)
            screen.blit(no_docs, (SCREEN_WIDTH // 2 - no_docs.get_width() // 2, list_y + 50))
        else:
            for i, doctor in enumerate(self.doctors):
                card_y = list_y + (i * 95) - self.scroll_y
                if list_y - 20 < card_y < SCREEN_HEIGHT - 150:
                    self.draw_doctor_card(screen, doctor, 20, card_y)
                    self.doctor_cards.append((pygame.Rect(20, card_y, SCREEN_WIDTH - 40, 85), doctor))

    def draw_doctor_card(self, screen, doctor, x, y):
        width = SCREEN_WIDTH - 40
        height = 85

        pygame.draw.rect(screen, COLOR_WHITE, (x, y, width, height), border_radius=12)
        pygame.draw.rect(screen, (230, 230, 230), (x, y, width, height), 1, border_radius=12)

        avatar_x = x + 45
        avatar_y = y + height // 2
        pygame.draw.circle(screen, BLUE, (avatar_x, avatar_y), 25)
        initial = doctor.name.split()[-1][0].upper()
        initial_text = FONT_MEDIUM.render(initial, True, COLOR_WHITE)
        screen.blit(initial_text, (avatar_x - initial_text.get_width() // 2, avatar_y - initial_text.get_height() // 2))

        name_text = FONT_MEDIUM.render(doctor.name, True, COLOR_BLACK)
        screen.blit(name_text, (x + 80, y + 15))

        spec_text = FONT_SMALL.render(doctor.specialty, True, GREY)
        screen.blit(spec_text, (x + 80, y + 40))

        patient_count = self.db.get_doctor_patient_count(doctor.id)
        patients_text = FONT_SMALL.render(f"{patient_count} patients", True, GREY)
        screen.blit(patients_text, (x + 80, y + 60))

        fee_text = FONT_SMALL.render(f"${doctor.consultation_fee:.0f}", True, GREEN)
        screen.blit(fee_text, (x + width - fee_text.get_width() - 40, y + 30))

        arrow = FONT_BODY.render(">", True, GREY)
        screen.blit(arrow, (x + width - 25, y + height // 2 - 10))

    def draw_doctor_detail(self, screen):
        if not self.selected_doctor:
            return

        doctor = self.selected_doctor

        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (20, 55))

        avatar_y = 130
        pygame.draw.circle(screen, BLUE, (SCREEN_WIDTH // 2, avatar_y), 45)
        initial = doctor.name.split()[-1][0].upper()
        initial_text = FONT_LARGE.render(initial, True, COLOR_WHITE)
        screen.blit(initial_text, (SCREEN_WIDTH // 2 - initial_text.get_width() // 2, avatar_y - 18))

        name_text = FONT_LARGE.render(doctor.name, True, COLOR_BLACK)
        screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, 195))

        spec_text = FONT_BODY.render(doctor.specialty, True, GREY)
        screen.blit(spec_text, (SCREEN_WIDTH // 2 - spec_text.get_width() // 2, 230))

        card_y = 270
        card_height = 150
        pygame.draw.rect(screen, COLOR_WHITE, (20, card_y, SCREEN_WIDTH - 40, card_height), border_radius=15)

        details = [
            ("📞", f"Phone: {doctor.phone}"),
            ("📧", f"Email: {doctor.email}"),
            ("💰", f"Fee: ${doctor.consultation_fee:.0f}"),
            ("📅", f"Available: {doctor.available_days}"),
            ("🕐", f"Hours: {doctor.available_hours}"),
        ]

        for i, (icon, text) in enumerate(details):
            detail_y = card_y + 15 + (i * 26)
            detail_text = FONT_SMALL.render(f"{icon}  {text}", True, COLOR_BLACK)
            screen.blit(detail_text, (35, detail_y))

        self.book_button_rect = pygame.Rect(20, 450, SCREEN_WIDTH - 40, 50)
        pygame.draw.rect(screen, BLUE, self.book_button_rect, border_radius=12)
        book_text = FONT_MEDIUM.render("Book Appointment", True, COLOR_WHITE)
        screen.blit(book_text, (SCREEN_WIDTH // 2 - book_text.get_width() // 2, 463))

    def draw_time_select(self, screen):
        back_text = FONT_BODY.render("< Back", True, BLUE)
        screen.blit(back_text, (20, 55))

        title = FONT_LARGE.render("Select Time", True, COLOR_BLACK)
        screen.blit(title, (20, 90))

        if self.selected_doctor:
            doctor_text = FONT_BODY.render(f"with {self.selected_doctor.name}", True, GREY)
            screen.blit(doctor_text, (20, 125))

        date_y = 165
        date_label = FONT_SMALL.render("Select Date:", True, GREY)
        screen.blit(date_label, (20, date_y - 20))

        self.date_buttons = []
        for i in range(7):
            date = datetime.now() + timedelta(days=i)
            btn_x = 20 + (i * 55)

            is_selected = self.selected_date and self.selected_date.date() == date.date()
            btn_color = BLUE if is_selected else COLOR_WHITE
            text_color = COLOR_WHITE if is_selected else COLOR_BLACK

            btn_rect = pygame.Rect(btn_x, date_y, 50, 70)
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
            if not is_selected:
                pygame.draw.rect(screen, (220, 220, 220), btn_rect, 1, border_radius=10)

            day_text = FONT_SMALL.render(date.strftime("%a"), True, text_color if is_selected else GREY)
            screen.blit(day_text, (btn_x + 25 - day_text.get_width() // 2, date_y + 10))

            num_text = FONT_MEDIUM.render(str(date.day), True, text_color)
            screen.blit(num_text, (btn_x + 25 - num_text.get_width() // 2, date_y + 35))

            self.date_buttons.append((btn_rect, date))

        time_y = 270
        times_label = FONT_SMALL.render("Available Times:", True, GREY)
        screen.blit(times_label, (20, time_y))

        time_slots = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]
        self.time_buttons = []

        time_y += 30
        for i, time in enumerate(time_slots):
            row = i // 4
            col = i % 4
            btn_width = (SCREEN_WIDTH - 70) // 4
            btn_x = 20 + (col * (btn_width + 10))
            btn_y = time_y + (row * 55)

            is_booked = time in self.booked_slots
            is_selected = self.selected_time == time

            if is_booked:
                btn_color = (240, 240, 240)
                text_color = (180, 180, 180)
            elif is_selected:
                btn_color = BLUE
                text_color = COLOR_WHITE
            else:
                btn_color = COLOR_WHITE
                text_color = COLOR_BLACK

            btn_rect = pygame.Rect(btn_x, btn_y, btn_width, 45)
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)

            if not is_selected and not is_booked:
                pygame.draw.rect(screen, (220, 220, 220), btn_rect, 1, border_radius=10)

            time_text = FONT_BODY.render(time, True, text_color)
            screen.blit(time_text, (btn_x + btn_width // 2 - time_text.get_width() // 2, btn_y + 12))

            if is_booked:
                booked_text = FONT_SMALL.render("Booked", True, RED)
                screen.blit(booked_text, (btn_x + btn_width // 2 - booked_text.get_width() // 2, btn_y + 28))

            if not is_booked:
                self.time_buttons.append((btn_rect, time))

        legend_y = time_y + 130
        pygame.draw.rect(screen, (240, 240, 240), (20, legend_y, 15, 15), border_radius=3)
        legend_text = FONT_SMALL.render("= Already booked", True, GREY)
        screen.blit(legend_text, (40, legend_y))

        if self.selected_date and self.selected_time:
            self.confirm_button_rect = pygame.Rect(20, 500, SCREEN_WIDTH - 40, 50)
            pygame.draw.rect(screen, GREEN, self.confirm_button_rect, border_radius=12)

            date_str = self.selected_date.strftime("%b %d")
            confirm_text = FONT_MEDIUM.render(f"Confirm: {date_str} at {self.selected_time}", True, COLOR_WHITE)
            screen.blit(confirm_text, (SCREEN_WIDTH // 2 - confirm_text.get_width() // 2, 513))

    def draw_confirmation(self, screen):
        center_x = SCREEN_WIDTH // 2

        pygame.draw.circle(screen, GREEN, (center_x, 180), 50)
        check = FONT_LARGE.render("✓", True, COLOR_WHITE)
        screen.blit(check, (center_x - check.get_width() // 2, 160))

        success_text = FONT_LARGE.render("Booking Confirmed!", True, COLOR_BLACK)
        screen.blit(success_text, (center_x - success_text.get_width() // 2, 260))

        card_y = 310
        card_height = 140
        pygame.draw.rect(screen, COLOR_WHITE, (20, card_y, SCREEN_WIDTH - 40, card_height), border_radius=15)

        if self.selected_doctor and self.selected_date:
            details = [
                ("👨‍⚕️", f"Doctor: {self.selected_doctor.name}"),
                ("🏥", f"Specialty: {self.selected_doctor.specialty}"),
                ("📅", f"Date: {self.selected_date.strftime('%B %d, %Y')}"),
                ("🕐", f"Time: {self.selected_time}"),
                ("💰", f"Fee: ${self.selected_doctor.consultation_fee:.0f}"),
            ]

            for i, (icon, text) in enumerate(details):
                detail_y = card_y + 15 + (i * 24)
                detail_text = FONT_SMALL.render(f"{icon}  {text}", True, COLOR_BLACK)
                screen.blit(detail_text, (35, detail_y))

        info_text = FONT_SMALL.render("You will receive a confirmation email shortly.", True, GREY)
        screen.blit(info_text, (center_x - info_text.get_width() // 2, 470))

        self.done_button_rect = pygame.Rect(20, 520, SCREEN_WIDTH - 40, 50)
        pygame.draw.rect(screen, BLUE, self.done_button_rect, border_radius=12)
        done_text = FONT_MEDIUM.render("Done", True, COLOR_WHITE)
        screen.blit(done_text, (center_x - done_text.get_width() // 2, 533))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if self.state == "list":
                if hasattr(self, 'search_rect') and self.search_rect.collidepoint(x, y):
                    self.search_active = True
                    return None
                else:
                    if self.search_active:
                        self.search_active = False

                if hasattr(self, 'specialty_chips'):
                    for chip_rect, specialty in self.specialty_chips:
                        if chip_rect.collidepoint(x, y):
                            self.selected_specialty = None if specialty == "All" else specialty
                            self.search_text = ""
                            self.load_doctors()
                            return None

                if hasattr(self, 'doctor_cards'):
                    for card_rect, doctor in self.doctor_cards:
                        if card_rect.collidepoint(x, y):
                            self.selected_doctor = doctor
                            self.state = "doctor_detail"
                            return None

            elif self.state == "doctor_detail":
                if y < 90 and x < 100:
                    self.state = "list"
                    self.selected_doctor = None
                    return None

                if hasattr(self, 'book_button_rect') and self.book_button_rect.collidepoint(x, y):
                    self.state = "time_select"
                    self.selected_date = datetime.now() + timedelta(days=1)
                    self.load_booked_slots()
                    return None

            elif self.state == "time_select":
                if y < 90 and x < 100:
                    self.state = "doctor_detail"
                    self.selected_date = None
                    self.selected_time = None
                    return None

                if hasattr(self, 'date_buttons'):
                    for btn_rect, date in self.date_buttons:
                        if btn_rect.collidepoint(x, y):
                            self.selected_date = date
                            self.selected_time = None
                            self.load_booked_slots()
                            return None

                if hasattr(self, 'time_buttons'):
                    for btn_rect, time in self.time_buttons:
                        if btn_rect.collidepoint(x, y):
                            self.selected_time = time
                            return None

                if hasattr(self, 'confirm_button_rect') and self.confirm_button_rect.collidepoint(x, y):
                    if self.selected_date and self.selected_time:
                        if self.db.is_time_slot_available(
                            self.selected_doctor.id,
                            self.selected_date,
                            self.selected_time
                        ):
                            self.book_appointment()
                            self.state = "confirm"
                    return None

            elif self.state == "confirm":
                if hasattr(self, 'done_button_rect') and self.done_button_rect.collidepoint(x, y):
                    self.reset()
                    return None

        elif event.type == pygame.MOUSEWHEEL:
            if self.state == "list":
                self.scroll_y -= event.y * 30
                self.scroll_y = max(0, self.scroll_y)

        elif event.type == pygame.KEYDOWN:
            if self.state == "list" and self.search_active:
                if event.key == pygame.K_BACKSPACE:
                    self.search_text = self.search_text[:-1]
                    self.load_doctors()
                elif event.key == pygame.K_RETURN:
                    self.search_active = False
                elif event.key == pygame.K_ESCAPE:
                    self.search_active = False
                    self.search_text = ""
                    self.load_doctors()
                elif event.unicode and event.unicode.isprintable():
                    self.search_text += event.unicode
                    self.load_doctors()
                return None

            if event.key == pygame.K_ESCAPE:
                if self.state == "list":
                    if self.search_active:
                        self.search_active = False
                elif self.state != "list":
                    self.state = "list"
                    self.selected_doctor = None
                    self.selected_date = None
                    self.selected_time = None

        return None

    def book_appointment(self):
        if self.selected_doctor and self.selected_date and self.selected_time:
            appointment = Appointment(
                patient_id=self.current_patient_id,
                doctor_id=self.selected_doctor.id,
                appointment_date=self.selected_date,
                appointment_time=self.selected_time,
                status="scheduled"
            )
            appointment_id = self.db.add_appointment(appointment)
            return appointment_id > 0
        return False

    def reset(self):
        self.state = "list"
        self.selected_doctor = None
        self.selected_date = None
        self.selected_time = None
        self.scroll_y = 0
        self.search_text = ""
        self.search_active = False
        self.booked_slots = []