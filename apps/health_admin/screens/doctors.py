import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK
from apps.shared import Database, Doctor, Validators
from apps.shared.models import SPECIALTIES

BLUE = (0, 122, 255)
RED = (255, 59, 48)
GREEN = (52, 199, 89)
ORANGE = (255, 149, 0)
PURPLE = (175, 82, 222)
PINK = (255, 45, 85)
GREY = (142, 142, 147)
LIGHT_BG = (245, 245, 250)

FONT_LARGE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_TINY = pygame.font.SysFont("Arial", 12)
FONT_BUTTON = pygame.font.SysFont("Arial", 17, bold=True)

NAVBAR_HEIGHT = 85


class DoctorsScreen:
    """Doctors management screen."""

    def __init__(self):
        self.db = Database()
        self.background_color = LIGHT_BG

        # Data
        self.doctors = []
        self.selected_doctor = None

        # View mode: list, view, add, edit
        self.mode = "list"

        # Search
        self.search_query = ""
        self.search_active = False

        # Scroll
        self.scroll_y = 0
        self.max_scroll = 0

        # Form fields
        self.fields = {}
        self.active_field = None
        self.dropdown_open = None
        self.field_touched = {}

        # Error animation
        self.error_heights = {}
        self.max_error_height = 18
        self.animation_speed = 2

        # Click areas
        self.card_rects = []
        self.button_rects = {}

        # Key repeat
        pygame.key.set_repeat(400, 50)

        self.reset_form()
        self.load_doctors()

    def reset_form(self):
        """Reset form fields."""
        self.fields = {
            "name": "",
            "email": "",
            "phone": "",
            "age": "",
            "specialty": "",
            "password": "",
        }
        self.field_touched = {k: False for k in self.fields}
        self.error_heights = {k: 0 for k in self.fields}
        self.active_field = None
        self.dropdown_open = None

    def load_doctors(self):
        """Load doctors from database."""
        if self.search_query:
            self.doctors = self.db.search_doctors(self.search_query)
        else:
            self.doctors = self.db.get_all_doctors(active_only=False)

    def populate_form(self, doctor):
        """Populate form with doctor data."""
        self.fields["name"] = doctor.name
        self.fields["email"] = doctor.email
        self.fields["phone"] = doctor.phone or ""
        self.fields["age"] = str(doctor.age) if doctor.age else ""
        self.fields["specialty"] = doctor.specialty or ""
        self.fields["password"] = ""

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
                    if age < 25 or age > 80:
                        return "Age must be between 25-80"
                except ValueError:
                    return "Enter a valid age"
        elif field_name == "specialty":
            if not value:
                return "Please select a specialty"
        elif field_name == "password":
            if self.mode == "add" and len(value) < 8:
                return "Password must be at least 8 characters"

        return None

    def is_form_valid(self):
        """Check if form is valid."""
        required_valid = (
            len(self.fields["name"].strip()) >= 2 and
            Validators.validate_email(self.fields["email"])[0] and
            self.fields["specialty"]
        )

        if self.mode == "add":
            required_valid = required_valid and len(self.fields["password"]) >= 8

        return required_valid

    def update_error_animations(self):
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

    def save_doctor(self):
        """Save doctor to database."""
        # Touch all fields
        for key in self.fields:
            self.field_touched[key] = True

        if not self.is_form_valid():
            return False

        if self.mode == "add":
            # Generate doctor number
            all_doctors = self.db.get_all_doctors(active_only=False)
            doctor_number = f"DOC{len(all_doctors) + 1:03d}"

            doctor = Doctor(
                name=self.fields["name"].strip(),
                email=self.fields["email"].strip(),
                phone=self.fields["phone"].strip(),
                age=int(self.fields["age"]) if self.fields["age"] else 0,
                specialty=self.fields["specialty"],
                doctor_number=doctor_number,
                password_hash=self.db.hash_password(self.fields["password"])
            )
            self.db.add_doctor(doctor)

        elif self.mode == "edit" and self.selected_doctor:
            self.selected_doctor.name = self.fields["name"].strip()
            self.selected_doctor.email = self.fields["email"].strip()
            self.selected_doctor.phone = self.fields["phone"].strip()
            self.selected_doctor.age = int(self.fields["age"]) if self.fields["age"] else 0
            self.selected_doctor.specialty = self.fields["specialty"]
            self.db.update_doctor(self.selected_doctor)

        self.mode = "list"
        self.reset_form()
        self.selected_doctor = None
        self.load_doctors()
        return True

    def delete_doctor(self, doctor_id):
        """Delete (deactivate) a doctor."""
        self.db.delete_doctor(doctor_id)
        self.load_doctors()

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
        # Add button
        if "add_btn" in self.button_rects:
            if self.button_rects["add_btn"].collidepoint(x, y):
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

        # Doctor cards
        for card_rect, doctor in self.card_rects:
            if card_rect.collidepoint(x, y):
                self.selected_doctor = doctor
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
                self.selected_doctor = None
                self.scroll_y = 0
                return None

        # Edit button
        if "edit_btn" in self.button_rects:
            if self.button_rects["edit_btn"].collidepoint(x, y):
                self.mode = "edit"
                self.populate_form(self.selected_doctor)
                self.scroll_y = 0
                return None

        # Delete button
        if "delete_btn" in self.button_rects:
            if self.button_rects["delete_btn"].collidepoint(x, y):
                self.delete_doctor(self.selected_doctor.id)
                self.mode = "list"
                self.selected_doctor = None
                return None

        return None

    def handle_form_click(self, x, y):
        """Handle clicks in add/edit mode."""
        # Back button
        if "back_btn" in self.button_rects:
            if self.button_rects["back_btn"].collidepoint(x, y):
                self.mode = "list"
                self.reset_form()
                self.selected_doctor = None
                self.scroll_y = 0
                return None

        # Save button
        if "save_btn" in self.button_rects:
            if self.button_rects["save_btn"].collidepoint(x, y):
                self.save_doctor()
                return None

        # Dropdown options
        if self.dropdown_open == "specialty" and "dropdown_options" in self.button_rects:
            for option_rect, option_value in self.button_rects["dropdown_options"]:
                if option_rect.collidepoint(x, y):
                    self.fields["specialty"] = option_value
                    self.field_touched["specialty"] = True
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
                if actual_field == "specialty":
                    self.dropdown_open = "specialty"
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
                self.load_doctors()
            elif event.key == pygame.K_RETURN:
                self.search_active = False
            elif event.key == pygame.K_ESCAPE:
                self.search_query = ""
                self.search_active = False
                self.load_doctors()
            elif event.unicode and event.unicode.isprintable():
                self.search_query += event.unicode
                self.load_doctors()

        elif self.mode in ["add", "edit"] and self.active_field:
            if event.key == pygame.K_BACKSPACE:
                self.fields[self.active_field] = self.fields[self.active_field][:-1]
            elif event.key == pygame.K_TAB:
                fields_order = ["name", "email", "phone", "age", "password"]
                if self.active_field in fields_order:
                    idx = fields_order.index(self.active_field)
                    self.field_touched[self.active_field] = True
                    self.active_field = fields_order[(idx + 1) % len(fields_order)]
                    self.field_touched[self.active_field] = True
            elif event.key == pygame.K_RETURN:
                self.save_doctor()
            elif event.key == pygame.K_ESCAPE:
                self.active_field = None
            elif event.unicode and event.unicode.isprintable():
                if len(self.fields[self.active_field]) < 100:
                    self.fields[self.active_field] += event.unicode

        elif event.key == pygame.K_ESCAPE:
            if self.mode in ["add", "edit", "view"]:
                self.mode = "list"
                self.reset_form()
                self.selected_doctor = None
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
        """Draw doctors list."""
        # Header
        title = FONT_LARGE.render("Doctors", True, COLOR_BLACK)
        screen.blit(title, (20, 55))

        # Add button
        add_btn = pygame.Rect(SCREEN_WIDTH - 50, 55, 35, 35)
        pygame.draw.rect(screen, BLUE, add_btn, border_radius=10)
        plus_font = pygame.font.SysFont("Arial", 24, bold=True)
        plus_text = plus_font.render("+", True, COLOR_WHITE)
        screen.blit(plus_text, (add_btn.x + 10, add_btn.y + 3))
        self.button_rects["add_btn"] = add_btn

        # Search bar
        search_y = 100
        search_rect = self.draw_search_field(screen, 15, search_y, SCREEN_WIDTH - 30)
        self.button_rects["search"] = search_rect

        # Doctors list
        list_y = 160 - self.scroll_y
        content_height = 0

        if not self.doctors:
            # Empty state
            empty_y = 250
            empty_text = FONT_BODY.render("No doctors found", True, GREY)
            screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, empty_y))

            if self.search_query:
                hint_text = FONT_SMALL.render("Try a different search term", True, GREY)
                screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, empty_y + 30))
        else:
            for i, doctor in enumerate(self.doctors):
                card_y = list_y + (i * 90)
                if 100 < card_y < SCREEN_HEIGHT - NAVBAR_HEIGHT - 20:
                    card_rect = self.draw_doctor_card(screen, doctor, 15, card_y, i)
                    self.card_rects.append((card_rect, doctor))
                content_height = (i + 1) * 90

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
                placeholder = FONT_BODY.render("Search doctors...", True, GREY)
                screen.blit(placeholder, (text_x, y + (height - placeholder.get_height()) // 2))

        return rect

    def draw_doctor_card(self, screen, doctor, x, y, index):
        """Draw a doctor card."""
        width = SCREEN_WIDTH - 30
        height = 80

        # Card background
        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=15)

        # Avatar
        colors = [BLUE, GREEN, PURPLE, ORANGE, PINK]
        avatar_color = colors[index % len(colors)]
        avatar_x = x + 35
        avatar_y = y + height // 2
        pygame.draw.circle(screen, avatar_color, (avatar_x, avatar_y), 25)

        # Initial
        name_parts = doctor.name.replace("Dr. ", "").split()
        initial = name_parts[0][0].upper() if name_parts else "D"
        initial_font = pygame.font.SysFont("Arial", 18, bold=True)
        initial_surface = initial_font.render(initial, True, COLOR_WHITE)
        screen.blit(initial_surface, (avatar_x - initial_surface.get_width() // 2,
                                       avatar_y - initial_surface.get_height() // 2))

        # Name
        name_text = FONT_MEDIUM.render(doctor.name, True, COLOR_BLACK)
        screen.blit(name_text, (x + 75, y + 18))

        # Specialty
        specialty_text = FONT_SMALL.render(doctor.specialty or "General", True, GREY)
        screen.blit(specialty_text, (x + 75, y + 45))

        # Status indicator
        status_color = GREEN if doctor.is_active else RED
        pygame.draw.circle(screen, status_color, (x + width - 25, y + height // 2), 6)

        # Chevron
        chevron_x = x + width - 50
        chevron_y = y + height // 2
        pygame.draw.line(screen, GREY, (chevron_x, chevron_y - 8), (chevron_x + 8, chevron_y), 2)
        pygame.draw.line(screen, GREY, (chevron_x + 8, chevron_y), (chevron_x, chevron_y + 8), 2)

        return card_rect

    def draw_view(self, screen):
        """Draw doctor detail view."""
        # Back button
        back_btn = self.draw_back_button(screen, 15, 55)
        self.button_rects["back_btn"] = back_btn

        # Title
        title = FONT_MEDIUM.render("Doctor Details", True, COLOR_BLACK)
        screen.blit(title, (70, 60))

        if not self.selected_doctor:
            return

        doctor = self.selected_doctor

        # Profile card
        card_y = 110
        card_height = 160
        card_rect = pygame.Rect(15, card_y, SCREEN_WIDTH - 30, card_height)
        pygame.draw.rect(screen, COLOR_WHITE, card_rect, border_radius=20)

        # Avatar
        avatar_x = SCREEN_WIDTH // 2
        avatar_y = card_y + 50
        pygame.draw.circle(screen, BLUE, (avatar_x, avatar_y), 40)

        name_parts = doctor.name.replace("Dr. ", "").split()
        initial = name_parts[0][0].upper() if name_parts else "D"
        initial_font = pygame.font.SysFont("Arial", 28, bold=True)
        initial_surface = initial_font.render(initial, True, COLOR_WHITE)
        screen.blit(initial_surface, (avatar_x - initial_surface.get_width() // 2,
                                       avatar_y - initial_surface.get_height() // 2))

        # Name
        name_text = FONT_LARGE.render(doctor.name, True, COLOR_BLACK)
        screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, card_y + 100))

        # Specialty badge
        if doctor.specialty:
            badge_width = len(doctor.specialty) * 8 + 20
            badge_x = SCREEN_WIDTH // 2 - badge_width // 2
            badge_y = card_y + 135
            pygame.draw.rect(screen, (230, 245, 255), (badge_x, badge_y, badge_width, 22), border_radius=11)
            spec_text = FONT_TINY.render(doctor.specialty, True, BLUE)
            screen.blit(spec_text, (badge_x + 10, badge_y + 4))

        # Details card
        details_y = card_y + card_height + 20
        details_height = 200
        details_rect = pygame.Rect(15, details_y, SCREEN_WIDTH - 30, details_height)
        pygame.draw.rect(screen, COLOR_WHITE, details_rect, border_radius=20)

        # Detail rows
        row_y = details_y + 20
        details = [
            ("Email", doctor.email, "📧"),
            ("Phone", doctor.phone or "Not provided", "📱"),
            ("Age", f"{doctor.age} years" if doctor.age else "Not provided", "🎂"),
            ("Doctor ID", doctor.doctor_number or "N/A", "🏷️"),
            ("Status", "Active" if doctor.is_active else "Inactive", "✅" if doctor.is_active else "❌"),
        ]

        for label, value, icon in details:
            self.draw_detail_row(screen, 30, row_y, label, value, icon)
            row_y += 35

        # Action buttons
        buttons_y = details_y + details_height + 30

        # Edit button
        edit_btn = pygame.Rect(15, buttons_y, (SCREEN_WIDTH - 40) // 2, 50)
        pygame.draw.rect(screen, BLUE, edit_btn, border_radius=12)
        edit_text = FONT_BUTTON.render("Edit", True, COLOR_WHITE)
        screen.blit(edit_text, (edit_btn.x + edit_btn.width // 2 - edit_text.get_width() // 2,
                                edit_btn.y + 13))
        self.button_rects["edit_btn"] = edit_btn

        # Delete button
        delete_btn = pygame.Rect(SCREEN_WIDTH // 2 + 5, buttons_y, (SCREEN_WIDTH - 40) // 2, 50)
        pygame.draw.rect(screen, COLOR_WHITE, delete_btn, border_radius=12)
        pygame.draw.rect(screen, RED, delete_btn, 2, border_radius=12)
        delete_text = FONT_BUTTON.render("Delete", True, RED)
        screen.blit(delete_text, (delete_btn.x + delete_btn.width // 2 - delete_text.get_width() // 2,
                                  delete_btn.y + 13))
        self.button_rects["delete_btn"] = delete_btn

    def draw_detail_row(self, screen, x, y, label, value, icon):
        """Draw a detail row."""
        # Icon
        try:
            icon_font = pygame.font.SysFont("Segoe UI Emoji", 16)
        except:
            icon_font = pygame.font.SysFont("Arial", 16)
        icon_surface = icon_font.render(icon, True, GREY)
        screen.blit(icon_surface, (x, y))

        # Label
        label_surface = FONT_SMALL.render(label, True, GREY)
        screen.blit(label_surface, (x + 30, y))

        # Value
        value_surface = FONT_SMALL.render(value, True, COLOR_BLACK)
        screen.blit(value_surface, (x + 120, y))

    def draw_form(self, screen):
        """Draw add/edit form."""
        # Back button
        back_btn = self.draw_back_button(screen, 15, 55)
        self.button_rects["back_btn"] = back_btn

        # Title
        title_text = "Add Doctor" if self.mode == "add" else "Edit Doctor"
        title = FONT_MEDIUM.render(title_text, True, COLOR_BLACK)
        screen.blit(title, (70, 60))

        # Form card
        form_y = 110
        form_rect = pygame.Rect(15, form_y, SCREEN_WIDTH - 30, 480)
        pygame.draw.rect(screen, COLOR_WHITE, form_rect, border_radius=20)

        current_y = form_y + 20
        field_width = SCREEN_WIDTH - 70

        # Name field
        current_y = self.draw_form_field(screen, "name", "Full Name (Dr.)", 35, current_y, field_width)

        # Email field
        current_y = self.draw_form_field(screen, "email", "Email Address", 35, current_y, field_width)

        # Phone field
        current_y = self.draw_form_field(screen, "phone", "Phone Number", 35, current_y, field_width)

        # Age field
        current_y = self.draw_form_field(screen, "age", "Age", 35, current_y, field_width)

        # Specialty dropdown
        current_y = self.draw_dropdown_field(screen, "specialty", "Specialty", 35, current_y, field_width)

        # Password field (only for add mode)
        if self.mode == "add":
            current_y = self.draw_form_field(screen, "password", "Password", 35, current_y, field_width, is_password=True)

        # Save button
        save_y = form_y + 430
        save_btn = pygame.Rect(35, save_y, field_width, 50)
        btn_color = BLUE if self.is_form_valid() else GREY
        pygame.draw.rect(screen, btn_color, save_btn, border_radius=12)
        save_text = FONT_BUTTON.render("Save Doctor", True, COLOR_WHITE)
        screen.blit(save_text, (save_btn.x + save_btn.width // 2 - save_text.get_width() // 2,
                                save_btn.y + 13))
        self.button_rects["save_btn"] = save_btn

        # Draw dropdown options on top
        if self.dropdown_open == "specialty":
            self.draw_dropdown_options(screen, 35, self.dropdown_y + 52, field_width)

    def draw_form_field(self, screen, field_name, placeholder, x, y, width, is_password=False):
        """Draw a form input field."""
        field_height = 50
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
        display_value = "•" * len(value) if is_password and value else value

        if display_value:
            text_surface = FONT_BODY.render(display_value, True, COLOR_BLACK)
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

        # Error message
        total_height = field_height + 10
        if error and error_height > 0:
            error_font = pygame.font.SysFont("Arial", 12)
            error_surface = error_font.render(error, True, RED)
            error_y = y + field_height + 3

            if error_height >= error_surface.get_height():
                screen.blit(error_surface, (x + 5, error_y))
            else:
                clip_rect = pygame.Rect(0, 0, error_surface.get_width(), int(error_height))
                screen.blit(error_surface, (x + 5, error_y), clip_rect)

            total_height += error_height

        return y + total_height

    def draw_dropdown_field(self, screen, field_name, placeholder, x, y, width):
        """Draw a dropdown field."""
        field_height = 50
        error = self.validate_field(field_name)
        error_height = self.error_heights.get(field_name, 0)

        self.dropdown_y = y

        # Border color
        if error and error_height > 0:
            border_color = RED
        elif self.dropdown_open == field_name:
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
            text_surface = FONT_BODY.render(value, True, COLOR_BLACK)
        else:
            text_surface = FONT_BODY.render(placeholder, True, GREY)
        screen.blit(text_surface, (x + 15, y + (field_height - text_surface.get_height()) // 2))

        # Arrow
        arrow = "▼" if self.dropdown_open != field_name else "▲"
        arrow_surface = FONT_BODY.render(arrow, True, GREY)
        screen.blit(arrow_surface, (x + width - 30, y + (field_height - arrow_surface.get_height()) // 2))

        # Error message
        total_height = field_height + 10
        if error and error_height > 0 and self.dropdown_open != field_name:
            error_font = pygame.font.SysFont("Arial", 12)
            error_surface = error_font.render(error, True, RED)
            screen.blit(error_surface, (x + 5, y + field_height + 3))
            total_height += error_height

        return y + total_height

    def draw_dropdown_options(self, screen, x, y, width):
        """Draw dropdown options."""
        visible_options = SPECIALTIES[:6]
        option_height = 44
        dropdown_height = len(visible_options) * option_height

        # Shadow
        pygame.draw.rect(screen, (200, 200, 200), (x + 3, y + 3, width, dropdown_height), border_radius=12)

        # Background
        pygame.draw.rect(screen, COLOR_WHITE, (x, y, width, dropdown_height), border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), (x, y, width, dropdown_height), 1, border_radius=12)

        # Options
        option_rects = []
        for i, option in enumerate(visible_options):
            option_y = y + (i * option_height)
            option_rect = pygame.Rect(x, option_y, width, option_height)
            option_rects.append((option_rect, option))

            # Highlight selected
            if option == self.fields["specialty"]:
                highlight = pygame.Surface((width - 8, option_height - 8), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (0, 122, 255, 30), (0, 0, width - 8, option_height - 8), border_radius=8)
                screen.blit(highlight, (x + 4, option_y + 4))

            # Option text
            option_surface = FONT_BODY.render(option, True, COLOR_BLACK)
            screen.blit(option_surface, (x + 15, option_y + (option_height - option_surface.get_height()) // 2))

            # Separator
            if i < len(visible_options) - 1:
                pygame.draw.line(screen, (240, 240, 240), (x + 15, option_y + option_height),
                               (x + width - 15, option_y + option_height), 1)

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