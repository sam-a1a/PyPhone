"""Patients management screen - matches Health app design."""
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database, Patient, Validators
from apps.shared.models import DISEASES

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


class PatientsScreen:

    def __init__(self):
        self.db = Database()
        self.background_color = LIGHT_BG

        self.is_admin = False
        self.is_doctor = False
        self.current_doctor_id = None

        self.patients = []
        self.doctors = []
        self.selected_patient = None

        self.mode = "list"

        self.search_query = ""
        self.search_active = False

        self.filter_disease = ""

        self.scroll_y = 0
        self.max_scroll = 0

        self.fields = {}
        self.active_field = None
        self.dropdown_open = None
        self.field_touched = {}

        self.error_heights = {}
        self.max_error_height = 18
        self.animation_speed = 2

        self.card_rects = []
        self.button_rects = {}

        self.dropdown_y = 0

        pygame.key.set_repeat(400, 50)

        self.reset_form()

    def reset_form(self):
        self.fields = {
            "name": "",
            "email": "",
            "phone": "",
            "age": "",
            "disease": "",
            "assigned_doctor": "",
            "medical_history": "",
        }
        self.field_touched = {k: False for k in self.fields}
        self.error_heights = {k: 0 for k in self.fields}
        self.active_field = None
        self.dropdown_open = None

    def load_data(self, doctor_id=None):
        if doctor_id is not None:
            self.is_admin = False
            self.is_doctor = True
            self.current_doctor_id = doctor_id
        else:
            self.is_admin = True
            self.is_doctor = False
            self.current_doctor_id = None

        if self.is_doctor and self.current_doctor_id:
            # Doctor view - only their patients
            if self.search_query:
                self.patients = self.db.search_patients_by_doctor(self.current_doctor_id, self.search_query)
            else:
                self.patients = self.db.get_patients_by_doctor(self.current_doctor_id)
        else:
            # Admin view - all patients
            if self.search_query:
                self.patients = self.db.search_patients(self.search_query)
            elif self.filter_disease:
                self.patients = self.db.get_patients_by_disease(self.filter_disease)
            else:
                self.patients = self.db.get_all_patients()

        # Always load doctors for dropdown (admin needs it for add/edit)
        self.doctors = self.db.get_all_doctors()

    def get_doctor_options(self):
        """Get doctor options for dropdown."""
        return [f"{d.name} ({d.specialty})" for d in self.doctors]

    def get_doctor_id_from_selection(self, selection):
        """Get doctor ID from selection string."""
        if not selection:
            return None
        for doctor in self.doctors:
            if f"{doctor.name} ({doctor.specialty})" == selection:
                return doctor.id
        return None

    def get_doctor_name_by_id(self, doctor_id):
        """Get doctor name by ID."""
        if not doctor_id:
            return "Not assigned"
        for doctor in self.doctors:
            if doctor.id == doctor_id:
                return doctor.name
        return "Unknown"

    def populate_form(self, patient):
        """Populate form with patient data."""
        self.fields["name"] = patient.name
        self.fields["email"] = patient.email
        self.fields["phone"] = patient.phone or ""
        self.fields["age"] = str(patient.age) if patient.age else ""
        self.fields["disease"] = patient.disease or ""
        self.fields["medical_history"] = patient.medical_history or ""

        # Find assigned doctor
        if patient.assigned_doctor_id:
            for doctor in self.doctors:
                if doctor.id == patient.assigned_doctor_id:
                    self.fields["assigned_doctor"] = f"{doctor.name} ({doctor.specialty})"
                    break

    def validate_field(self, field_name):
        """Validate a single field."""
        if not self.field_touched.get(field_name, False):
            return None

        value = self.fields.get(field_name, "")

        if field_name == "name":
            if len(value.strip()) < 2:
                return "Name must be at least 2 characters"
        elif field_name == "email":
            if not value:
                return "Email is required"
            is_valid, _ = Validators.validate_email(value)
            if not is_valid:
                return "Please enter a valid email"
        elif field_name == "phone":
            if value and len(value) < 10:
                return "Enter a valid phone number"
        elif field_name == "age":
            if value:
                try:
                    age = int(value)
                    if age < 0 or age > 120:
                        return "Age must be between 0-120"
                except ValueError:
                    return "Enter a valid age"

        return None

    def is_form_valid(self):
        """Check if form is valid."""
        return (
            len(self.fields["name"].strip()) >= 2 and
            Validators.validate_email(self.fields["email"])[0]
        )

    def update_error_animations(self):
        """Update error animations."""
        for field_name in self.fields:
            error = self.validate_field(field_name)
            if error:
                self.error_heights[field_name] = min(
                    self.error_heights[field_name] + self.animation_speed,
                    self.max_error_height
                )
            else:
                self.error_heights[field_name] = max(
                    self.error_heights[field_name] - self.animation_speed,
                    0
                )

    def save_patient(self):
        """Save patient to database."""
        # Touch required fields
        for key in ["name", "email"]:
            self.field_touched[key] = True

        if not self.is_form_valid():
            return False

        assigned_doctor_id = self.get_doctor_id_from_selection(self.fields["assigned_doctor"])

        if self.mode == "add":
            # Only admin can add - but double check
            if not self.is_admin:
                return False

            # Generate patient number
            all_patients = self.db.get_all_patients()
            patient_number = f"PAT{len(all_patients) + 1:03d}"

            patient = Patient(
                name=self.fields["name"].strip(),
                email=self.fields["email"].strip(),
                phone=self.fields["phone"].strip(),
                age=int(self.fields["age"]) if self.fields["age"] else 0,
                patient_number=patient_number,
                disease=self.fields["disease"],
                assigned_doctor_id=assigned_doctor_id,
                medical_history=self.fields["medical_history"]
            )
            self.db.add_patient(patient)

        elif self.mode == "edit" and self.selected_patient:
            self.selected_patient.name = self.fields["name"].strip()
            self.selected_patient.email = self.fields["email"].strip()
            self.selected_patient.phone = self.fields["phone"].strip()
            self.selected_patient.age = int(self.fields["age"]) if self.fields["age"] else 0
            self.selected_patient.disease = self.fields["disease"]
            self.selected_patient.medical_history = self.fields["medical_history"]

            # Only admin can change assigned doctor
            if self.is_admin:
                self.selected_patient.assigned_doctor_id = assigned_doctor_id

            self.db.update_patient(self.selected_patient)

        self.mode = "list"
        self.reset_form()
        self.selected_patient = None

        # Reload with current context
        if self.is_doctor:
            self.load_data(doctor_id=self.current_doctor_id)
        else:
            self.load_data()

        return True

    def delete_patient(self, patient_id):
        """Delete a patient. Only admin can do this."""
        if not self.is_admin:
            return False

        self.db.delete_patient(patient_id)

        # Reload with current context
        if self.is_doctor:
            self.load_data(doctor_id=self.current_doctor_id)
        else:
            self.load_data()

        return True

    def handle_event(self, event):
        """Handle events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if self.mode == "list":
                return self.handle_list_click(x, y)
            elif self.mode == "view":
                return self.handle_view_click(x, y)
            elif self.mode in ["add", "edit"]:
                return self.handle_form_click(x, y)

        elif event.type == pygame.KEYDOWN:
            return self.handle_keydown(event)

        elif event.type == pygame.MOUSEWHEEL:
            if self.mode == "list":
                self.scroll_y -= event.y * 30
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))

        return None

    def handle_list_click(self, x, y):
        """Handle clicks in list mode."""
        # Add button (admin only)
        if "add_btn" in self.button_rects:
            if self.button_rects["add_btn"].collidepoint(x, y):
                if self.is_admin:
                    self.mode = "add"
                    self.reset_form()
                    self.scroll_y = 0
                return None

        # Search field
        if "search" in self.button_rects:
            if self.button_rects["search"].collidepoint(x, y):
                self.search_active = True
                return None
            else:
                self.search_active = False

        # Patient cards
        for card_rect, patient in self.card_rects:
            if card_rect.collidepoint(x, y):
                self.selected_patient = patient
                self.mode = "view"
                self.scroll_y = 0
                return None

        return None

    def handle_view_click(self, x, y):
        """Handle clicks in view mode."""
        # Back button
        if "back_btn" in self.button_rects:
            if self.button_rects["back_btn"].collidepoint(x, y):
                self.mode = "list"
                self.selected_patient = None
                self.scroll_y = 0
                return None

        # Edit button
        if "edit_btn" in self.button_rects:
            if self.button_rects["edit_btn"].collidepoint(x, y):
                self.mode = "edit"
                self.populate_form(self.selected_patient)
                self.scroll_y = 0
                return None

        # Delete button (admin only)
        if "delete_btn" in self.button_rects:
            if self.button_rects["delete_btn"].collidepoint(x, y):
                if self.is_admin:
                    self.delete_patient(self.selected_patient.id)
                    self.mode = "list"
                    self.selected_patient = None
                return None

        return None

    def handle_form_click(self, x, y):
        """Handle clicks in add/edit mode."""
        # Back button
        if "back_btn" in self.button_rects:
            if self.button_rects["back_btn"].collidepoint(x, y):
                self.mode = "list"
                self.reset_form()
                self.selected_patient = None
                self.scroll_y = 0
                return None

        # Save button
        if "save_btn" in self.button_rects:
            if self.button_rects["save_btn"].collidepoint(x, y):
                self.save_patient()
                return None

        # Dropdown options
        if self.dropdown_open and "dropdown_options" in self.button_rects:
            for option_rect, option_value in self.button_rects["dropdown_options"]:
                if option_rect.collidepoint(x, y):
                    self.fields[self.dropdown_open] = option_value
                    self.field_touched[self.dropdown_open] = True
                    self.dropdown_open = None
                    return None

        # Close dropdown if clicking elsewhere
        if self.dropdown_open:
            self.dropdown_open = None
            return None

        # Field clicks
        for field_name, rect in self.button_rects.items():
            if field_name.startswith("field_") and rect.collidepoint(x, y):
                actual_field = field_name.replace("field_", "")

                # Doctor cannot change assigned_doctor field
                if actual_field == "assigned_doctor" and self.is_doctor:
                    return None

                if actual_field in ["disease", "assigned_doctor"]:
                    self.dropdown_open = actual_field
                    self.active_field = None
                else:
                    self.active_field = actual_field
                    self.field_touched[actual_field] = True
                    self.dropdown_open = None
                return None

        self.active_field = None
        return None

    def handle_keydown(self, event):
        """Handle keyboard input."""
        if self.mode == "list" and self.search_active:
            if event.key == pygame.K_BACKSPACE:
                self.search_query = self.search_query[:-1]
                # Reload with current context
                if self.is_doctor:
                    self.load_data(doctor_id=self.current_doctor_id)
                else:
                    self.load_data()
            elif event.key == pygame.K_RETURN:
                self.search_active = False
            elif event.key == pygame.K_ESCAPE:
                self.search_query = ""
                self.search_active = False
                # Reload with current context
                if self.is_doctor:
                    self.load_data(doctor_id=self.current_doctor_id)
                else:
                    self.load_data()
            elif event.unicode and event.unicode.isprintable():
                self.search_query += event.unicode
                # Reload with current context
                if self.is_doctor:
                    self.load_data(doctor_id=self.current_doctor_id)
                else:
                    self.load_data()

        elif self.mode in ["add", "edit"] and self.active_field:
            if event.key == pygame.K_BACKSPACE:
                self.fields[self.active_field] = self.fields[self.active_field][:-1]
            elif event.key == pygame.K_TAB:
                fields_order = ["name", "email", "phone", "age", "medical_history"]
                if self.active_field in fields_order:
                    idx = fields_order.index(self.active_field)
                    self.field_touched[self.active_field] = True
                    self.active_field = fields_order[(idx + 1) % len(fields_order)]
                    self.field_touched[self.active_field] = True
            elif event.key == pygame.K_RETURN:
                self.save_patient()
            elif event.key == pygame.K_ESCAPE:
                self.active_field = None
            elif event.unicode and event.unicode.isprintable():
                if len(self.fields[self.active_field]) < 200:
                    self.fields[self.active_field] += event.unicode

        elif event.key == pygame.K_ESCAPE:
            if self.mode in ["add", "edit", "view"]:
                self.mode = "list"
                self.reset_form()
                self.selected_patient = None
                self.scroll_y = 0

        return None

    def update(self):
        """Update animations."""
        if self.mode in ["add", "edit"]:
            self.update_error_animations()

    def draw(self, screen):
        """Draw the screen."""
        screen.fill(self.background_color)

        self.button_rects = {}
        self.card_rects = []

        if self.mode == "list":
            self.draw_list(screen)
        elif self.mode == "view":
            self.draw_view(screen)
        elif self.mode in ["add", "edit"]:
            self.draw_form(screen)

    def draw_list(self, screen):
        """Draw patients list."""
        # Header - different title for admin vs doctor
        if self.is_admin:
            title_text = "All Patients"
        else:
            title_text = "My Patients"

        title = FONT_LARGE.render(title_text, True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        # Role badge
        badge_x = 20 + title.get_width() + 10
        badge_y = 60
        if self.is_admin:
            pygame.draw.rect(screen, PURPLE, (badge_x, badge_y, 55, 20), border_radius=10)
            badge_text = FONT_TINY.render("ADMIN", True, COLOR_WHITE)
        else:
            pygame.draw.rect(screen, TEAL, (badge_x, badge_y, 60, 20), border_radius=10)
            badge_text = FONT_TINY.render("DOCTOR", True, COLOR_WHITE)
        screen.blit(badge_text, (badge_x + 8, badge_y + 4))

        # Count badge
        count = len(self.patients)
        if count > 0:
            count_text = FONT_TINY.render(str(count), True, COLOR_WHITE)
            count_badge_x = badge_x + (55 if self.is_admin else 60) + 8
            badge_width = max(22, count_text.get_width() + 12)
            pygame.draw.rect(screen, GREEN, (count_badge_x, badge_y, badge_width, 20), border_radius=10)
            screen.blit(count_text, (count_badge_x + badge_width // 2 - count_text.get_width() // 2, badge_y + 4))

        # Add button (admin only)
        if self.is_admin:
            add_btn = pygame.Rect(SCREEN_WIDTH - 50, 55, 35, 35)
            pygame.draw.rect(screen, GREEN, add_btn, border_radius=10)
            plus_font = pygame.font.SysFont("Arial", 24, bold=True)
            plus_text = plus_font.render("+", True, COLOR_WHITE)
            screen.blit(plus_text, (add_btn.x + 10, add_btn.y + 3))
            self.button_rects["add_btn"] = add_btn

        # Search bar
        search_y = 100
        search_rect = self.draw_search_field(screen, 15, search_y, SCREEN_WIDTH - 30)
        self.button_rects["search"] = search_rect

        # Patients list
        list_y = 160 - self.scroll_y
        content_height = 0

        if not self.patients:
            # Empty state
            empty_y = 250
            if self.is_doctor:
                empty_text = FONT_BODY.render("No patients assigned to you", True, GREY)
            else:
                empty_text = FONT_BODY.render("No patients found", True, GREY)
            screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, empty_y))

            if self.search_query:
                hint_text = FONT_SMALL.render("Try a different search term", True, GREY)
                screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, empty_y + 30))
            elif self.is_admin:
                hint_text = FONT_SMALL.render("Tap + to add a patient", True, BLUE)
                screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, empty_y + 30))
        else:
            for i, patient in enumerate(self.patients):
                card_y = list_y + (i * 95)
                if 100 < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 20:
                    card_rect = self.draw_patient_card(screen, patient, 15, card_y, i)
                    self.card_rects.append((card_rect, patient))
                content_height = (i + 1) * 95

        self.max_scroll = max(0, content_height - (SCREEN_HEIGHT - NAVBAR_HEIGHT - 180))

    def draw_search_field(self, screen, x, y, width):
        """Draw search field."""
        height = 44
        rect = pygame.Rect(x, y, width, height)

        # Background
        pygame.draw.rect(screen, COLOR_WHITE, rect, border_radius=12)

        # Border
        border_color = BLUE if self.search_active else (220, 220, 220)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=12)

        # Search icon
        icon_x = x + 15
        icon_y = y + height // 2
        pygame.draw.circle(screen, GREY, (icon_x, icon_y - 2), 8, 2)
        pygame.draw.line(screen, GREY, (icon_x + 5, icon_y + 3), (icon_x + 10, icon_y + 8), 2)

        # Text or placeholder
        text_x = x + 38
        if self.search_query:
            text_surface = FONT_BODY.render(self.search_query, True, COLOR_BLACK)
            screen.blit(text_surface, (text_x, y + (height - text_surface.get_height()) // 2))

            if self.search_active:
                cursor_x = text_x + text_surface.get_width() + 2
                pygame.draw.line(screen, COLOR_BLACK, (cursor_x, y + 10), (cursor_x, y + height - 10), 2)
        else:
            if self.search_active:
                pygame.draw.line(screen, COLOR_BLACK, (text_x, y + 10), (text_x, y + height - 10), 2)
            else:
                if self.is_doctor:
                    placeholder = FONT_BODY.render("Search my patients...", True, GREY)
                else:
                    placeholder = FONT_BODY.render("Search all patients...", True, GREY)
                screen.blit(placeholder, (text_x, y + (height - placeholder.get_height()) // 2))

        return rect

    def draw_patient_card(self, screen, patient, x, y, index):
        """Draw a patient card."""
        width = SCREEN_WIDTH - 30
        height = 85

        # Card background
        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

        # Avatar
        colors = [GREEN, BLUE, PURPLE, ORANGE, PINK]
        avatar_color = colors[index % len(colors)]
        avatar_x = x + 35
        avatar_y = y + height // 2
        pygame.draw.circle(screen, avatar_color, (avatar_x, avatar_y), 25)

        # Initial
        initial = patient.name[0].upper() if patient.name else "P"
        initial_font = pygame.font.SysFont("Arial", 18, bold=True)
        initial_surface = initial_font.render(initial, True, COLOR_WHITE)
        screen.blit(initial_surface, (avatar_x - initial_surface.get_width() // 2,
                                       avatar_y - initial_surface.get_height() // 2))

        # Name
        name_text = FONT_MEDIUM.render(patient.name, True, COLOR_BLACK)
        screen.blit(name_text, (x + 75, y + 15))

        # Disease
        disease = patient.disease if patient.disease else "No condition"
        disease_text = FONT_SMALL.render(disease, True, GREY)
        screen.blit(disease_text, (x + 75, y + 40))

        # Assigned doctor (only show for admin view)
        if self.is_admin:
            doctor_name = self.get_doctor_name_by_id(patient.assigned_doctor_id)
            if len(doctor_name) > 20:
                doctor_name = doctor_name[:18] + "..."
            doctor_text = FONT_TINY.render(f"Dr: {doctor_name}", True, BLUE)
            screen.blit(doctor_text, (x + 75, y + 62))

        # Chevron
        chevron_x = x + width - 30
        chevron_y = y + height // 2
        pygame.draw.line(screen, GREY, (chevron_x, chevron_y - 8), (chevron_x + 8, chevron_y), 2)
        pygame.draw.line(screen, GREY, (chevron_x + 8, chevron_y), (chevron_x, chevron_y + 8), 2)

        return card_rect

    def draw_view(self, screen):
        """Draw patient detail view."""
        # Back button
        back_btn = self.draw_back_button(screen, 15, 55)
        self.button_rects["back_btn"] = back_btn

        # Title
        title = FONT_MEDIUM.render("Patient Details", True, COLOR_BLACK)
        screen.blit(title, (70, 60))

        if not self.selected_patient:
            return

        patient = self.selected_patient

        # Profile card
        card_y = 110
        card_height = 140
        card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, card_height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=20)

        # Avatar
        avatar_x = SCREEN_WIDTH // 2
        avatar_y = card_y + 45
        pygame.draw.circle(screen, GREEN, (avatar_x, avatar_y), 35)

        initial = patient.name[0].upper() if patient.name else "P"
        initial_font = pygame.font.SysFont("Arial", 24, bold=True)
        initial_surface = initial_font.render(initial, True, COLOR_WHITE)
        screen.blit(initial_surface, (avatar_x - initial_surface.get_width() // 2,
                                       avatar_y - initial_surface.get_height() // 2))

        # Name
        name_text = FONT_LARGE.render(patient.name, True, COLOR_BLACK)
        screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, card_y + 90))

        # Disease badge
        if patient.disease:
            badge_width = len(patient.disease) * 8 + 20
            badge_x = SCREEN_WIDTH // 2 - badge_width // 2
            badge_y = card_y + 120
            pygame.draw.rect(screen, (255, 240, 240), (badge_x, badge_y, badge_width, 22), border_radius=11)
            disease_text = FONT_TINY.render(patient.disease, True, RED)
            screen.blit(disease_text, (badge_x + 10, badge_y + 4))

        # Details card
        details_y = card_y + card_height + 20
        details_height = 220
        details_rect = pygame.Rect(15, details_y, SCREEN_WIDTH - 30, details_height)
        pygame.draw.rect(screen, COLOR_WHITE, details_rect, border_radius=20)

        # Detail rows
        row_y = details_y + 20
        doctor_name = self.get_doctor_name_by_id(patient.assigned_doctor_id)

        details = [
            ("Email", patient.email, "📧"),
            ("Phone", patient.phone or "Not provided", "📱"),
            ("Age", f"{patient.age} years" if patient.age else "Not provided", "🎂"),
            ("Patient ID", patient.patient_number or "N/A", "🏷️"),
            ("Doctor", doctor_name, "👨‍⚕️"),
            ("History", patient.medical_history[:30] + "..." if patient.medical_history and len(patient.medical_history) > 30 else patient.medical_history or "None", "📋"),
        ]

        for label, value, icon in details:
            self.draw_detail_row(screen, 30, row_y, label, value, icon)
            row_y += 33

        # Action buttons
        buttons_y = details_y + details_height + 25

        if self.is_admin:
            # Admin: Edit and Delete buttons
            edit_btn = pygame.Rect(15, buttons_y, (SCREEN_WIDTH - 40) // 2, 50)
            pygame.draw.rect(screen, BLUE, edit_btn, border_radius=12)
            edit_text = FONT_BUTTON.render("Edit", True, COLOR_WHITE)
            screen.blit(edit_text, (edit_btn.x + edit_btn.width // 2 - edit_text.get_width() // 2,
                                    edit_btn.y + 13))
            self.button_rects["edit_btn"] = edit_btn

            delete_btn = pygame.Rect(SCREEN_WIDTH // 2 + 5, buttons_y, (SCREEN_WIDTH - 40) // 2, 50)
            pygame.draw.rect(screen, COLOR_WHITE, delete_btn, border_radius=12)
            pygame.draw.rect(screen, RED, delete_btn, 2, border_radius=12)
            delete_text = FONT_BUTTON.render("Delete", True, RED)
            screen.blit(delete_text, (delete_btn.x + delete_btn.width // 2 - delete_text.get_width() // 2,
                                      delete_btn.y + 13))
            self.button_rects["delete_btn"] = delete_btn
        else:
            # Doctor: Only Edit button (full width)
            edit_btn = pygame.Rect(15, buttons_y, SCREEN_WIDTH - 30, 50)
            pygame.draw.rect(screen, BLUE, edit_btn, border_radius=12)
            edit_text = FONT_BUTTON.render("Edit Patient Info", True, COLOR_WHITE)
            screen.blit(edit_text, (edit_btn.x + edit_btn.width // 2 - edit_text.get_width() // 2,
                                    edit_btn.y + 13))
            self.button_rects["edit_btn"] = edit_btn

    def draw_detail_row(self, screen, x, y, label, value, icon):
        """Draw a detail row."""
        # Icon
        try:
            icon_font = pygame.font.SysFont("Segoe UI Emoji", 14)
        except:
            icon_font = pygame.font.SysFont("Arial", 14)
        icon_surface = icon_font.render(icon, True, GREY)
        screen.blit(icon_surface, (x, y))

        # Label
        label_surface = FONT_TINY.render(label, True, GREY)
        screen.blit(label_surface, (x + 28, y + 2))

        # Value
        value_str = str(value) if value else "N/A"
        if len(value_str) > 25:
            value_str = value_str[:22] + "..."
        value_surface = FONT_TINY.render(value_str, True, COLOR_BLACK)
        screen.blit(value_surface, (x + 100, y + 2))

    def draw_form(self, screen):
        """Draw add/edit form."""
        # Back button
        back_btn = self.draw_back_button(screen, 15, 55)
        self.button_rects["back_btn"] = back_btn

        # Title - different for add vs edit
        if self.mode == "add":
            title_text = "Add Patient"
        else:
            title_text = "Edit Patient"
        title = FONT_MEDIUM.render(title_text, True, COLOR_BLACK)
        screen.blit(title, (70, 60))

        # Form card
        form_y = 105
        form_rect = pygame.Rect(15, form_y, SCREEN_WIDTH - 30, 520)
        pygame.draw.rect(screen, COLOR_WHITE, form_rect, border_radius=20)

        current_y = form_y + 15
        field_width = SCREEN_WIDTH - 70

        # Name field
        current_y = self.draw_form_field(screen, "name", "Full Name", 35, current_y, field_width)

        # Email field
        current_y = self.draw_form_field(screen, "email", "Email Address", 35, current_y, field_width)

        # Phone and Age in row
        half_width = (field_width - 10) // 2
        phone_y = current_y
        self.draw_form_field(screen, "phone", "Phone", 35, current_y, half_width)
        current_y = self.draw_form_field(screen, "age", "Age", 35 + half_width + 10, phone_y, half_width)

        # Disease dropdown
        current_y = self.draw_dropdown_field(screen, "disease", "Condition/Disease", 35, current_y, field_width, DISEASES[:8])

        # Assigned doctor dropdown (admin only, or show as read-only for doctor)
        if self.is_admin:
            current_y = self.draw_dropdown_field(screen, "assigned_doctor", "Assigned Doctor", 35, current_y, field_width, self.get_doctor_options())
        else:
            # Doctor: Show assigned doctor as read-only
            current_y = self.draw_readonly_field(screen, "Assigned Doctor", self.fields.get("assigned_doctor", "You"), 35, current_y, field_width)

        # Medical history
        current_y = self.draw_form_field(screen, "medical_history", "Medical History Notes", 35, current_y, field_width)

        # Save button
        save_y = form_y + 465
        save_btn = pygame.Rect(35, save_y, field_width, 50)
        btn_color = BLUE if self.is_form_valid() else GREY
        pygame.draw.rect(screen, btn_color, save_btn, border_radius=12)
        save_text = FONT_BUTTON.render("Save Patient", True, COLOR_WHITE)
        screen.blit(save_text, (save_btn.x + save_btn.width // 2 - save_text.get_width() // 2,
                                save_btn.y + 13))
        self.button_rects["save_btn"] = save_btn

        # Draw dropdown options on top
        if self.dropdown_open:
            options = DISEASES[:6] if self.dropdown_open == "disease" else self.get_doctor_options()[:4]
            self.draw_dropdown_options(screen, 35, self.dropdown_y + 50, field_width, options)

    def draw_readonly_field(self, screen, label, value, x, y, width):
        """Draw a read-only field (for doctor view)."""
        field_height = 48

        # Input box (greyed out)
        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, (235, 235, 240), input_rect, border_radius=10)
        pygame.draw.rect(screen, (200, 200, 200), input_rect, 2, border_radius=10)

        # Value
        if value:
            text_surface = FONT_BODY.render(value, True, GREY)
        else:
            text_surface = FONT_BODY.render(label, True, GREY)
        screen.blit(text_surface, (x + 12, y + (field_height - text_surface.get_height()) // 2))

        # Lock icon
        lock_text = FONT_TINY.render("🔒", True, GREY)
        screen.blit(lock_text, (x + width - 30, y + (field_height - lock_text.get_height()) // 2))

        return y + field_height + 8

    def draw_form_field(self, screen, field_name, placeholder, x, y, width):
        """Draw a form input field."""
        field_height = 48
        error = self.validate_field(field_name)
        error_height = self.error_heights.get(field_name, 0)

        # Border color
        if error and error_height > 0:
            border_color = RED
        elif self.active_field == field_name:
            border_color = BLUE
        else:
            border_color = (220, 220, 220)

        # Input box
        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, LIGHT_BG, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)
        self.button_rects[f"field_{field_name}"] = input_rect

        # Value or placeholder
        value = self.fields.get(field_name, "")
        if value:
            display_value = value if len(value) <= 35 else value[:32] + "..."
            text_surface = FONT_BODY.render(display_value, True, COLOR_BLACK)
            screen.blit(text_surface, (x + 12, y + (field_height - text_surface.get_height()) // 2))

            if self.active_field == field_name:
                cursor_x = x + 12 + min(text_surface.get_width(), width - 30)
                pygame.draw.line(screen, COLOR_BLACK, (cursor_x, y + 10), (cursor_x, y + field_height - 10), 2)
        else:
            if self.active_field == field_name:
                pygame.draw.line(screen, COLOR_BLACK, (x + 12, y + 10), (x + 12, y + field_height - 10), 2)
            else:
                placeholder_surface = FONT_BODY.render(placeholder, True, GREY)
                screen.blit(placeholder_surface, (x + 12, y + (field_height - placeholder_surface.get_height()) // 2))

        # Error message
        total_height = field_height + 8
        if error and error_height > 0:
            error_font = pygame.font.SysFont("Arial", 11)
            error_surface = error_font.render(error, True, RED)
            screen.blit(error_surface, (x + 5, y + field_height + 2))
            total_height += error_height

        return y + total_height

    def draw_dropdown_field(self, screen, field_name, placeholder, x, y, width, options):
        """Draw a dropdown field."""
        field_height = 48

        self.dropdown_y = y if self.dropdown_open == field_name else self.dropdown_y

        # Border color
        if self.dropdown_open == field_name:
            border_color = BLUE
        else:
            border_color = (220, 220, 220)

        # Input box
        input_rect = pygame.Rect(x, y, width, field_height)
        pygame.draw.rect(screen, LIGHT_BG, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=10)
        self.button_rects[f"field_{field_name}"] = input_rect

        # Value or placeholder
        value = self.fields.get(field_name, "")
        if value:
            display_value = value if len(value) <= 30 else value[:27] + "..."
            text_surface = FONT_BODY.render(display_value, True, COLOR_BLACK)
        else:
            text_surface = FONT_BODY.render(placeholder, True, GREY)
        screen.blit(text_surface, (x + 12, y + (field_height - text_surface.get_height()) // 2))

        # Arrow
        arrow = "▼" if self.dropdown_open != field_name else "▲"
        arrow_surface = FONT_BODY.render(arrow, True, GREY)
        screen.blit(arrow_surface, (x + width - 28, y + (field_height - arrow_surface.get_height()) // 2))

        return y + field_height + 8

    def draw_dropdown_options(self, screen, x, y, width, options):
        """Draw dropdown options."""
        visible_options = options[:5]
        option_height = 42
        dropdown_height = len(visible_options) * option_height

        # Shadow
        pygame.draw.rect(screen, (200, 200, 200), (x + 3, y + 3, width, dropdown_height), border_radius=12)

        # Background
        pygame.draw.rect(screen, COLOR_WHITE, (x, y, width, dropdown_height), border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), (x, y, width, dropdown_height), 1, border_radius=12)

        # Options
        option_rects = []
        current_value = self.fields.get(self.dropdown_open, "")

        for i, option in enumerate(visible_options):
            option_y = y + (i * option_height)
            option_rect = pygame.Rect(x, option_y, width, option_height)
            option_rects.append((option_rect, option))

            # Highlight selected
            if option == current_value:
                highlight = pygame.Surface((width - 8, option_height - 8), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (0, 122, 255, 30), (0, 0, width - 8, option_height - 8), border_radius=8)
                screen.blit(highlight, (x + 4, option_y + 4))

            # Option text
            display_option = option if len(option) <= 35 else option[:32] + "..."
            option_surface = FONT_SMALL.render(display_option, True, COLOR_BLACK)
            screen.blit(option_surface, (x + 12, option_y + (option_height - option_surface.get_height()) // 2))

            # Separator
            if i < len(visible_options) - 1:
                pygame.draw.line(screen, (240, 240, 240), (x + 12, option_y + option_height),
                               (x + width - 12, option_y + option_height), 1)

        self.button_rects["dropdown_options"] = option_rects

    def draw_back_button(self, screen, x, y):
        """Draw back button."""
        back_rect = pygame.Rect(x, y, 45, 35)
        pygame.draw.rect(screen, (240, 240, 245), back_rect, border_radius=10)

        # Arrow
        arrow_x = x + 15
        arrow_y = y + 17
        pygame.draw.line(screen, BLUE, (arrow_x + 8, arrow_y - 6), (arrow_x, arrow_y), 2)
        pygame.draw.line(screen, BLUE, (arrow_x, arrow_y), (arrow_x + 8, arrow_y + 6), 2)

        return back_rect