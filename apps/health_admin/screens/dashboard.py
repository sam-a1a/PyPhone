import pygame
import math
from datetime import datetime
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database

# Colors - Same as Health app
BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
ORANGE = (255, 149, 0)
PINK = (255, 45, 85)
PURPLE = (175, 82, 222)
TEAL = (90, 200, 250)
GREY = (142, 142, 147)
LIGHT_BG = (245, 245, 250)

FONT_LARGE = pygame.font.SysFont("Arial", 26, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 12)

NAVBAR_HEIGHT = 85

HEADER_HEIGHT = 90


class DashboardScreen:
    """Dashboard screen - different views for Admin vs Doctor."""

    def __init__(self):
        self.db = Database()
        self.background_color = LIGHT_BG

        # User context
        self.user_role = None  # "admin" or "doctor"
        self.current_user_id = None
        self.current_doctor = None

        # Data - Admin view
        self.system_stats = {}
        self.all_doctors = []
        self.recent_appointments = []

        # Data - Doctor view
        self.doctor_stats = {}
        self.today_appointments = []
        self.my_patients = []

        # Scroll
        self.scroll_y = 0
        self.max_scroll = 300

        # Button rects for click handling
        self.button_rects = {}

    def load_data(self, context=None):

        if context is None:
            context = {
                "role": self.db.get_current_user_type(),
                "user_id": self.db.get_current_user_id(),
                "is_admin": self.db.is_admin(),
                "is_doctor": self.db.is_doctor(),
            }

        self.user_role = context.get("role")
        self.current_user_id = context.get("user_id")
        self.current_doctor = context.get("doctor")

        if context.get("is_admin"):
            self._load_admin_data()
        else:
            self._load_doctor_data()

    def _load_admin_data(self):
        self.system_stats = self.db.get_statistics()

        # All doctors
        self.all_doctors = self.db.get_all_doctors()[:5]

        # Recent appointments (all)
        all_appointments = self.db.get_all_appointments()
        today = datetime.now().date()
        self.recent_appointments = [
            a for a in all_appointments
            if a.appointment_date and a.appointment_date.date() == today
        ][:5]

    def _load_doctor_data(self):
        """Load data for doctor dashboard."""
        if not self.current_user_id:
            return

        doctor_id = self.current_user_id

        # Doctor's personal statistics
        self.doctor_stats = self.db.get_doctor_statistics(doctor_id)

        # Get doctor object if not passed
        if not self.current_doctor:
            self.current_doctor = self.db.get_doctor(doctor_id)

        # Today's appointments for this doctor
        all_appointments = self.db.get_appointments_by_doctor(doctor_id)
        today = datetime.now().date()
        self.today_appointments = [
            a for a in all_appointments
            if a.appointment_date and a.appointment_date.date() == today and a.status == 'scheduled'
        ][:3]

        # My patients
        self.my_patients = self.db.get_patients_by_doctor(doctor_id)[:3]

    def handle_event(self, event):
        """Handle events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            # Check logout button
            if "logout_btn" in self.button_rects:
                if self.button_rects["logout_btn"].collidepoint(x, y):
                    return "logout"

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 25
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))

        return None

    def update(self):
        """Update screen state."""
        pass

    def draw(self, screen):
        """Draw the dashboard based on user role."""
        screen.fill(self.background_color)

        # Reset button rects
        self.button_rects = {}

        if self.user_role == "admin":
            self._draw_admin_dashboard(screen)
        else:
            self._draw_doctor_dashboard(screen)

    # ========== ADMIN DASHBOARD ==========

    def _draw_admin_dashboard(self, screen):
        """Draw admin dashboard with system-wide view."""
        # Header
        self._draw_admin_header(screen)

        # Scrollable content
        content_start_y = HEADER_HEIGHT + 50
        content_y = content_start_y - self.scroll_y

        # System stats cards (2x2 grid)
        content_y = self._draw_admin_stats(screen, content_y)

        # Doctors overview
        content_y = self._draw_doctors_overview(screen, content_y + 20)

        # Today's appointments (all)
        content_y = self._draw_admin_appointments(screen, content_y + 20)

        # Update max scroll
        self.max_scroll = max(0, content_y + self.scroll_y - SCREEN_HEIGHT + NAVBAR_HEIGHT + 50)

    def _draw_admin_header(self, screen):
        """Draw admin header."""
        header_rect = pygame.Rect(0, 40, SCREEN_WIDTH, HEADER_HEIGHT)
        pygame.draw.rect(screen, self.background_color, header_rect)

        # Title with admin badge
        title = FONT_LARGE.render("Admin Dashboard", True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        # Admin badge
        badge_x = 20 + title.get_width() + 10
        badge_y = 60
        pygame.draw.rect(screen, PURPLE, (badge_x, badge_y, 55, 20), border_radius=10)
        badge_text = FONT_TINY.render("ADMIN", True, COLOR_WHITE)
        screen.blit(badge_text, (badge_x + 10, badge_y + 4))

        # Logout button (top right)
        logout_btn = pygame.Rect(SCREEN_WIDTH - 75, 55, 60, 30)
        pygame.draw.rect(screen, COLOR_WHITE, logout_btn, border_radius=8)
        pygame.draw.rect(screen, RED, logout_btn, 2, border_radius=8)
        logout_text = FONT_TINY.render("Logout", True, RED)
        screen.blit(logout_text, (logout_btn.x + (logout_btn.width - logout_text.get_width()) // 2,
                                  logout_btn.y + (logout_btn.height - logout_text.get_height()) // 2))
        self.button_rects["logout_btn"] = logout_btn

        # Date (below logout)
        today = datetime.now().strftime("%b %d, %Y")
        date_text = FONT_TINY.render(today, True, GREY)
        screen.blit(date_text, (SCREEN_WIDTH - date_text.get_width() - 15, 90))

    def _draw_admin_stats(self, screen, y):
        """Draw system-wide statistics cards for admin."""
        if y > SCREEN_HEIGHT - NAVBAR_HEIGHT or y + 220 < HEADER_HEIGHT:
            return y + 220

        card_width = (SCREEN_WIDTH - 50) // 2
        card_height = 95

        stats_data = [
            {
                "title": "Total Doctors",
                "value": str(self.system_stats.get("total_doctors", 0)),
                "subtitle": "Active staff",
                "color": BLUE,
                "icon": "👨‍⚕️"
            },
            {
                "title": "Total Patients",
                "value": str(self.system_stats.get("total_patients", 0)),
                "subtitle": "Registered",
                "color": GREEN,
                "icon": "👥"
            },
            {
                "title": "Today",
                "value": str(self.system_stats.get("today_appointments", 0)),
                "subtitle": "Appointments",
                "color": ORANGE,
                "icon": "📅"
            },
            {
                "title": "Pending",
                "value": str(self.system_stats.get("pending_appointments", 0)),
                "subtitle": "Scheduled",
                "color": PURPLE,
                "icon": "⏳"
            },
        ]

        for i, stat in enumerate(stats_data):
            col = i % 2
            row = i // 2

            card_x = 15 + col * (card_width + 10)
            card_y = y + row * (card_height + 10)

            if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 10:
                self._draw_stat_card(screen, card_x, card_y, card_width, card_height, stat)

        return y + (card_height + 10) * 2

    def _draw_doctors_overview(self, screen, y):
        """Draw doctors overview section for admin."""
        section_height = 35 + (len(self.all_doctors) * 55) + 20

        if y > SCREEN_HEIGHT - NAVBAR_HEIGHT or y + section_height < HEADER_HEIGHT:
            return y + section_height

        # Section header
        if y > HEADER_HEIGHT:
            header = FONT_MEDIUM.render("Doctors", True, COLOR_BLACK)
            screen.blit(header, (20, y))

            # Count badge
            count = len(self.all_doctors)
            count_text = FONT_TINY.render(str(count), True, COLOR_WHITE)
            badge_x = 20 + header.get_width() + 8
            pygame.draw.rect(screen, BLUE, (badge_x, y + 4, 22, 18), border_radius=9)
            screen.blit(count_text, (badge_x + 11 - count_text.get_width() // 2, y + 5))

        card_y = y + 35

        if not self.all_doctors:
            if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT:
                card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, 60)
                pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)
                no_docs = FONT_BODY.render("No doctors registered", True, GREY)
                screen.blit(no_docs, (SCREEN_WIDTH // 2 - no_docs.get_width() // 2, card_y + 20))
            return y + 35 + 60

        # Doctors card
        if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT:
            card_height = 15 + (len(self.all_doctors) * 55)
            card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, card_height)
            pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

            doc_y = card_y + 10
            for i, doctor in enumerate(self.all_doctors):
                self._draw_doctor_row(screen, doctor, 25, doc_y, i)
                doc_y += 55

            return y + 35 + card_height

        return y + section_height

    def _draw_doctor_row(self, screen, doctor, x, y, index):
        """Draw a doctor row in admin view."""
        colors = [BLUE, GREEN, PURPLE, ORANGE, PINK]
        avatar_color = colors[index % len(colors)]

        # Avatar
        avatar_x = x + 20
        avatar_y = y + 22
        pygame.draw.circle(screen, avatar_color, (avatar_x, avatar_y), 18)

        # Initial
        name_parts = doctor.name.replace("Dr. ", "").split()
        initial = name_parts[0][0].upper() if name_parts else "D"
        initial_font = pygame.font.SysFont("Arial", 14, bold=True)
        initial_surface = initial_font.render(initial, True, COLOR_WHITE)
        screen.blit(initial_surface, (avatar_x - initial_surface.get_width() // 2,
                                       avatar_y - initial_surface.get_height() // 2))

        # Name
        name_text = FONT_BODY.render(doctor.name, True, COLOR_BLACK)
        screen.blit(name_text, (x + 50, y + 5))

        # Specialty
        specialty = doctor.specialty or "General"
        spec_text = FONT_SMALL.render(specialty, True, GREY)
        screen.blit(spec_text, (x + 50, y + 26))

        # Patient count
        patient_count = self.db.get_doctor_patient_count(doctor.id)
        count_text = FONT_TINY.render(f"{patient_count} patients", True, BLUE)
        screen.blit(count_text, (SCREEN_WIDTH - 100, y + 15))

        # Separator
        if index < len(self.all_doctors) - 1:
            pygame.draw.line(screen, (240, 240, 240), (x + 50, y + 50), (SCREEN_WIDTH - 45, y + 50), 1)

    def _draw_admin_appointments(self, screen, y):
        """Draw today's appointments section for admin (all appointments)."""
        if not self.recent_appointments:
            section_height = 110
        else:
            section_height = 35 + (len(self.recent_appointments) * 70)

        if y > SCREEN_HEIGHT - NAVBAR_HEIGHT or y + section_height < HEADER_HEIGHT:
            return y + section_height

        # Section header
        if y > HEADER_HEIGHT:
            header = FONT_MEDIUM.render("Today's Appointments", True, COLOR_BLACK)
            screen.blit(header, (20, y))

            count = len(self.recent_appointments)
            if count > 0:
                count_text = FONT_TINY.render(str(count), True, COLOR_WHITE)
                badge_x = 20 + header.get_width() + 8
                badge_width = max(22, count_text.get_width() + 12)
                pygame.draw.rect(screen, ORANGE, (badge_x, y + 4, badge_width, 18), border_radius=9)
                screen.blit(count_text, (badge_x + badge_width // 2 - count_text.get_width() // 2, y + 5))

        card_y = y + 35

        if not self.recent_appointments:
            if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT:
                card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, 70)
                pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

                no_appt = FONT_BODY.render("No appointments today", True, GREY)
                screen.blit(no_appt, (SCREEN_WIDTH // 2 - no_appt.get_width() // 2, card_y + 25))

            return y + 35 + 70
        else:
            for i, appt in enumerate(self.recent_appointments):
                appt_y = card_y + (i * 70)
                if HEADER_HEIGHT < appt_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 10:
                    self._draw_admin_appointment_card(screen, appt, 15, appt_y)

            return y + 35 + (len(self.recent_appointments) * 70)

    def _draw_admin_appointment_card(self, screen, appt, x, y):
        """Draw appointment card for admin view (shows doctor name)."""
        width = SCREEN_WIDTH - 30
        height = 65

        pygame.draw.rect(screen, COLOR_WHITE, (x, y, width, height), border_radius=12)

        # Left color bar
        pygame.draw.rect(screen, ORANGE, (x, y, 5, height),
                        border_top_left_radius=12, border_bottom_left_radius=12)

        # Patient name
        patient_text = FONT_MEDIUM.render(appt.patient_name or "Patient", True, COLOR_BLACK)
        screen.blit(patient_text, (x + 15, y + 10))

        # Doctor name
        doctor_name = f"Dr. {appt.doctor_name}" if hasattr(appt, 'doctor_name') and appt.doctor_name else "Doctor"
        doctor_text = FONT_SMALL.render(doctor_name, True, BLUE)
        screen.blit(doctor_text, (x + 15, y + 35))

        # Time
        time_text = FONT_MEDIUM.render(appt.appointment_time, True, ORANGE)
        screen.blit(time_text, (x + width - time_text.get_width() - 15, y + 20))

    # ========== DOCTOR DASHBOARD ==========

    def _draw_doctor_dashboard(self, screen):
        """Draw doctor dashboard with personal view."""
        # Header
        self._draw_doctor_header(screen)

        # Scrollable content
        content_start_y = HEADER_HEIGHT + 50
        content_y = content_start_y - self.scroll_y

        # Personal stats
        content_y = self._draw_doctor_stats(screen, content_y)

        # Activity rings
        content_y = self._draw_activity_section(screen, content_y + 15)

        # Today's appointments (mine only)
        content_y = self._draw_my_appointments(screen, content_y + 15)

        # My patients
        content_y = self._draw_my_patients(screen, content_y + 15)

        # Update max scroll
        self.max_scroll = max(0, content_y + self.scroll_y - SCREEN_HEIGHT + NAVBAR_HEIGHT + 50)

    def _draw_doctor_header(self, screen):
        """Draw doctor header with welcome message."""
        header_rect = pygame.Rect(0, 40, SCREEN_WIDTH, HEADER_HEIGHT)
        pygame.draw.rect(screen, self.background_color, header_rect)

        # Welcome message
        if self.current_doctor:
            name_parts = self.current_doctor.name.replace("Dr. ", "").split()
            first_name = name_parts[0] if name_parts else "Doctor"
            welcome_text = f"Welcome, {first_name}!"
        else:
            welcome_text = "My Dashboard"

        title = FONT_LARGE.render(welcome_text, True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        # Doctor badge
        badge_x = 20 + title.get_width() + 10
        badge_y = 60
        pygame.draw.rect(screen, TEAL, (badge_x, badge_y, 60, 20), border_radius=10)
        badge_text = FONT_TINY.render("DOCTOR", True, COLOR_WHITE)
        screen.blit(badge_text, (badge_x + 8, badge_y + 4))

        # Logout button (top right)
        logout_btn = pygame.Rect(SCREEN_WIDTH - 75, 55, 60, 30)
        pygame.draw.rect(screen, COLOR_WHITE, logout_btn, border_radius=8)
        pygame.draw.rect(screen, RED, logout_btn, 2, border_radius=8)
        logout_text = FONT_TINY.render("Logout", True, RED)
        screen.blit(logout_text, (logout_btn.x + (logout_btn.width - logout_text.get_width()) // 2,
                                  logout_btn.y + (logout_btn.height - logout_text.get_height()) // 2))
        self.button_rects["logout_btn"] = logout_btn

        # Date (below logout)
        today = datetime.now().strftime("%b %d")
        date_text = FONT_TINY.render(today, True, GREY)
        screen.blit(date_text, (SCREEN_WIDTH - date_text.get_width() - 15, 90))

    def _draw_doctor_stats(self, screen, y):
        """Draw doctor's personal statistics."""
        if y > SCREEN_HEIGHT - NAVBAR_HEIGHT or y + 220 < HEADER_HEIGHT:
            return y + 220

        card_width = (SCREEN_WIDTH - 50) // 2
        card_height = 95

        stats_data = [
            {
                "title": "My Patients",
                "value": str(self.doctor_stats.get("total_patients", 0)),
                "subtitle": "Under care",
                "color": BLUE,
                "icon": "👥"
            },
            {
                "title": "Today",
                "value": str(self.doctor_stats.get("today_appointments", 0)),
                "subtitle": "Appointments",
                "color": GREEN,
                "icon": "📅"
            },
            {
                "title": "Upcoming",
                "value": str(self.doctor_stats.get("upcoming_appointments", 0)),
                "subtitle": "Scheduled",
                "color": ORANGE,
                "icon": "⏳"
            },
            {
                "title": "Completed",
                "value": str(self.doctor_stats.get("completed_appointments", 0)),
                "subtitle": "This month",
                "color": PURPLE,
                "icon": "✅"
            },
        ]

        for i, stat in enumerate(stats_data):
            col = i % 2
            row = i // 2

            card_x = 15 + col * (card_width + 10)
            card_y = y + row * (card_height + 10)

            if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 10:
                self._draw_stat_card(screen, card_x, card_y, card_width, card_height, stat)

        return y + (card_height + 10) * 2

    def _draw_activity_section(self, screen, y):
        """Draw activity rings section for doctor."""
        section_height = 180

        if y > SCREEN_HEIGHT - NAVBAR_HEIGHT or y + section_height < HEADER_HEIGHT:
            return y + section_height

        # Section header
        if y > HEADER_HEIGHT:
            header = FONT_MEDIUM.render("Activity", True, COLOR_BLACK)
            screen.blit(header, (20, y))

        # Activity card
        card_y = y + 30
        card_height = 140
        card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, card_height)

        if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT:
            pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

            # Activity rings
            ring_center_x = 85
            ring_center_y = card_y + card_height // 2

            # Calculate progress values
            total_appts = self.doctor_stats.get("upcoming_appointments", 0) + self.doctor_stats.get("completed_appointments", 0)
            completed = self.doctor_stats.get("completed_appointments", 0)
            patients = self.doctor_stats.get("total_patients", 0)

            appt_progress = min(1.0, completed / max(1, total_appts))
            patient_progress = min(1.0, patients / 20)
            today_progress = min(1.0, self.doctor_stats.get("today_appointments", 0) / 10)

            # Draw rings
            self._draw_activity_ring(screen, (ring_center_x, ring_center_y), 45, RED, appt_progress)
            self._draw_activity_ring(screen, (ring_center_x, ring_center_y), 33, GREEN, patient_progress)
            self._draw_activity_ring(screen, (ring_center_x, ring_center_y), 21, BLUE, today_progress)

            # Legend
            legend_x = 155
            legend_y = card_y + 25

            legends = [
                {"color": RED, "label": "Appointments", "value": f"{int(appt_progress * 100)}%"},
                {"color": GREEN, "label": "Patients", "value": f"{patients}/20"},
                {"color": BLUE, "label": "Today", "value": f"{self.doctor_stats.get('today_appointments', 0)}"},
            ]

            for legend in legends:
                pygame.draw.circle(screen, legend["color"], (legend_x, legend_y + 6), 5)
                label = FONT_SMALL.render(legend["label"], True, COLOR_BLACK)
                screen.blit(label, (legend_x + 12, legend_y - 2))
                value = FONT_SMALL.render(legend["value"], True, GREY)
                screen.blit(value, (legend_x + 130, legend_y - 2))
                legend_y += 32

        return y + 30 + card_height

    def _draw_activity_ring(self, screen, center, radius, color, progress):
        """Draw a single activity ring."""
        pygame.draw.circle(screen, (230, 230, 230), center, radius, 7)

        if progress > 0:
            num_segments = max(1, int(50 * progress))
            for i in range(num_segments):
                angle = (math.pi / 2) - (2 * math.pi * progress * i / num_segments)
                x1 = center[0] + int((radius - 3) * math.cos(angle))
                y1 = center[1] - int((radius - 3) * math.sin(angle))
                x2 = center[0] + int((radius + 3) * math.cos(angle))
                y2 = center[1] - int((radius + 3) * math.sin(angle))
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)

    def _draw_my_appointments(self, screen, y):
        """Draw today's appointments section for doctor (only theirs)."""
        if not self.today_appointments:
            section_height = 110
        else:
            section_height = 35 + (len(self.today_appointments) * 70)

        if y > SCREEN_HEIGHT - NAVBAR_HEIGHT or y + section_height < HEADER_HEIGHT:
            return y + section_height

        # Section header
        if y > HEADER_HEIGHT:
            header = FONT_MEDIUM.render("My Appointments Today", True, COLOR_BLACK)
            screen.blit(header, (20, y))

            count = len(self.today_appointments)
            if count > 0:
                count_text = FONT_TINY.render(str(count), True, COLOR_WHITE)
                badge_x = 20 + header.get_width() + 8
                badge_width = max(22, count_text.get_width() + 12)
                pygame.draw.rect(screen, BLUE, (badge_x, y + 4, badge_width, 18), border_radius=9)
                screen.blit(count_text, (badge_x + badge_width // 2 - count_text.get_width() // 2, y + 5))

        card_y = y + 35

        if not self.today_appointments:
            if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT:
                card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, 70)
                pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

                no_appt = FONT_BODY.render("No appointments today", True, GREY)
                screen.blit(no_appt, (SCREEN_WIDTH // 2 - no_appt.get_width() // 2, card_y + 15))

                relax_text = FONT_SMALL.render("Enjoy your free time! 🎉", True, GREY)
                screen.blit(relax_text, (SCREEN_WIDTH // 2 - relax_text.get_width() // 2, card_y + 42))

            return y + 35 + 70
        else:
            for i, appt in enumerate(self.today_appointments):
                appt_y = card_y + (i * 70)
                if HEADER_HEIGHT < appt_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 10:
                    self._draw_doctor_appointment_card(screen, appt, 15, appt_y)

            return y + 35 + (len(self.today_appointments) * 70)

    def _draw_doctor_appointment_card(self, screen, appt, x, y):
        """Draw appointment card for doctor view."""
        width = SCREEN_WIDTH - 30
        height = 65

        pygame.draw.rect(screen, BLUE, (x, y, width, height), border_radius=12)

        # Patient name
        patient_text = FONT_MEDIUM.render(appt.patient_name or "Patient", True, COLOR_WHITE)
        screen.blit(patient_text, (x + 15, y + 12))

        # Notes
        notes = appt.notes if appt.notes else "General consultation"
        if len(notes) > 28:
            notes = notes[:25] + "..."
        notes_text = FONT_SMALL.render(notes, True, (200, 220, 255))
        screen.blit(notes_text, (x + 15, y + 38))

        # Time
        time_text = FONT_MEDIUM.render(appt.appointment_time, True, COLOR_WHITE)
        screen.blit(time_text, (x + width - time_text.get_width() - 15, y + 20))

    def _draw_my_patients(self, screen, y):
        """Draw my patients section for doctor."""
        if not self.my_patients:
            section_height = 100
        else:
            section_height = 35 + 25 + (len(self.my_patients) * 50)

        if y > SCREEN_HEIGHT - NAVBAR_HEIGHT or y + section_height < HEADER_HEIGHT:
            return y + section_height

        if y > HEADER_HEIGHT:
            header = FONT_MEDIUM.render("My Patients", True, COLOR_BLACK)
            screen.blit(header, (20, y))

        card_y = y + 30

        if not self.my_patients:
            if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT:
                card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, 60)
                pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

                no_patients = FONT_BODY.render("No patients assigned yet", True, GREY)
                screen.blit(no_patients, (SCREEN_WIDTH // 2 - no_patients.get_width() // 2, card_y + 20))

            return y + 30 + 60
        else:
            if HEADER_HEIGHT < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT:
                card_height = 20 + (len(self.my_patients) * 50)
                card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, card_height)
                pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

                patient_y = card_y + 12
                for i, patient in enumerate(self.my_patients):
                    self._draw_patient_row(screen, patient, 30, patient_y, i)
                    patient_y += 50

                return y + 30 + card_height

        return y + 30 + 60

    def _draw_patient_row(self, screen, patient, x, y, index):
        """Draw a single patient row."""
        colors = [BLUE, GREEN, PURPLE, ORANGE, PINK]
        avatar_color = colors[index % len(colors)]

        # Avatar
        avatar_x = x + 18
        avatar_y = y + 18
        pygame.draw.circle(screen, avatar_color, (avatar_x, avatar_y), 16)

        # Initial
        initial = patient.name[0].upper() if patient.name else "?"
        initial_font = pygame.font.SysFont("Arial", 12, bold=True)
        initial_surface = initial_font.render(initial, True, COLOR_WHITE)
        screen.blit(initial_surface, (avatar_x - initial_surface.get_width() // 2,
                                       avatar_y - initial_surface.get_height() // 2))

        # Name
        name_text = FONT_BODY.render(patient.name, True, COLOR_BLACK)
        screen.blit(name_text, (x + 48, y + 3))

        # Disease
        disease = patient.disease if patient.disease else "General checkup"
        if len(disease) > 25:
            disease = disease[:22] + "..."
        disease_text = FONT_SMALL.render(disease, True, GREY)
        screen.blit(disease_text, (x + 48, y + 24))

        # Separator
        if index < len(self.my_patients) - 1:
            line_y = y + 45
            pygame.draw.line(screen, (240, 240, 240), (x + 48, line_y), (SCREEN_WIDTH - 45, line_y), 1)

    # ========== SHARED COMPONENTS ==========

    def _draw_stat_card(self, screen, x, y, width, height, stat):
        """Draw a single stat card (shared by admin and doctor)."""
        # Card background
        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

        # Colored accent bar on left
        accent_rect = pygame.Rect(x, y, 5, height)
        pygame.draw.rect(screen, stat["color"], accent_rect,
                        border_top_left_radius=15, border_bottom_left_radius=15)

        # Icon
        try:
            icon_font = pygame.font.SysFont("Segoe UI Emoji", 18)
        except:
            icon_font = pygame.font.SysFont("Arial", 18)
        icon_surface = icon_font.render(stat["icon"], True, stat["color"])
        screen.blit(icon_surface, (x + 15, y + 12))

        # Title
        title_surface = FONT_TINY.render(stat["title"], True, GREY)
        screen.blit(title_surface, (x + 15, y + 38))

        # Value
        value_surface = FONT_LARGE.render(stat["value"], True, stat["color"])
        screen.blit(value_surface, (x + width - value_surface.get_width() - 15, y + 22))

        # Subtitle
        sub_surface = FONT_TINY.render(stat["subtitle"], True, GREY)
        screen.blit(sub_surface, (x + 15, y + 58))