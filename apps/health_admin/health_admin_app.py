#Health Admin App
import pygame

from apps.base_app import BaseApp
from apps.health_admin.components import BottomNavbar
from apps.health_admin.screens import (
    AdminOnboardingScreen,
    AdminLoginScreen,
    AdminSignupScreen,
    AdminTermsScreen,
    AdminForgotPasswordScreen,
    DashboardScreen,
    DoctorsScreen,
    PatientsScreen,
    AppointmentsScreen,
    ReportsScreen,
    AppleSignInModal,
    GoogleSignInModal
)
from apps.shared import Database
from components import draw_status_bar


class HealthAdminApp(BaseApp):
    #Hospital App

    def __init__(self, screen):
        super().__init__(screen)
        self.app_name = "Health Admin"
        self.db = Database()
        self.user_role = None  # Will be "admin" or "doctor" after login

        # Initialize auth screens
        self.screens = {
            "onboarding": AdminOnboardingScreen(),
            "login": AdminLoginScreen(),
            "signup": AdminSignupScreen(),
            "terms": AdminTermsScreen(),
            "forgot_password": AdminForgotPasswordScreen(),
        }

        # Tab screens (after login)
        self.tab_screens = {
            "home": DashboardScreen(),
            "doctors": DoctorsScreen(),
            "patients": PatientsScreen(),
            "appointments": AppointmentsScreen(),
            "reports": ReportsScreen(),
        }

        # Check if already logged in via Session (Persistence)
        if self.db.is_logged_in():
            user_type = self.db.get_current_user_type()
            if user_type == "doctor":
                self.current_screen = "home"
                self.show_navbar = True
                self.user_role = "doctor"
                self.current_doctor = self.db.get_current_doctor()
                self.navbar = BottomNavbar()
                self.navbar.set_admin_mode(False)
                # Load initial data
                self.refresh_tab_data("home")
            elif user_type == "admin":
                self.current_screen = "home"
                self.show_navbar = True
                self.user_role = "admin"
                self.current_doctor = None
                self.navbar = BottomNavbar()
                self.navbar.set_admin_mode(True)
                # Load initial data
                self.refresh_tab_data("home")
            else:
                self.current_screen = "onboarding"
                self.show_navbar = False
                self.current_doctor = None
                self.navbar = BottomNavbar()
        else:
            self.current_screen = "onboarding"
            self.show_navbar = False
            self.current_doctor = None
            self.navbar = BottomNavbar()

        self.last_tab = None

        # Modal overlays
        self.apple_modal = AppleSignInModal()
        self.google_modal = GoogleSignInModal()
        self.active_modal = None

    def refresh_tab_data(self, tab_name):
        # Determine Doctor ID (if logged in as doctor)
        doc_id = None
        if self.user_role == "doctor" and self.current_doctor:
            doc_id = self.current_doctor.id

        if tab_name == "home":
            # Pass explicit context to dashboard
            context = {
                "role": self.user_role,
                "user_id": doc_id if self.user_role == "doctor" else None,
                "doctor": self.current_doctor,
                "is_admin": self.user_role == "admin",
                "is_doctor": self.user_role == "doctor"
            }
            self.tab_screens["home"].load_data(context)

        elif tab_name == "doctors":
            self.tab_screens["doctors"].load_doctors()

        elif tab_name == "patients":
            self.tab_screens["patients"].load_data(doctor_id=doc_id)

        elif tab_name == "appointments":
            self.tab_screens["appointments"].load_appointments(doctor_id=doc_id)

        elif tab_name == "reports":
            pass

    def save_login(self):
        #Save login session after social auth
        doctors = self.db.get_all_doctors()
        if doctors:
            doctor = doctors[0]
            self.db.save_session("doctor", doctor.id, doctor.email)
            self.current_doctor = doctor
            self.user_role = "doctor"

    def logout(self):
        #Logout and clear session
        self.db.clear_session()
        self.show_navbar = False
        self.current_screen = "onboarding"
        self.current_doctor = None
        self.user_role = None

        # Reset screens
        self.screens["login"].reset()
        self.screens["signup"].reset()
        if hasattr(self.screens["onboarding"], 'current_page'):
            self.screens["onboarding"].current_page = 0

    def draw(self):
        if self.show_navbar:
            current_tab = self.navbar.get_selected_tab_name()
            if current_tab != self.last_tab:
                self.refresh_tab_data(current_tab)
                self.last_tab = current_tab

        if self.show_navbar:
            tab_name = self.navbar.get_selected_tab_name()
            if tab_name in self.tab_screens:
                self.tab_screens[tab_name].draw(self.screen)

            self.navbar.draw(self.screen)
        else:
            current = self.screens[self.current_screen]
            current.draw(self.screen)

        draw_status_bar(self.screen, dark_mode=False)
        self.draw_bezel()

        if self.active_modal == "apple":
            result = self.apple_modal.update()
            self.apple_modal.draw(self.screen)
            if result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.save_login()
                self.navbar.set_admin_mode(False)  # Social login = doctor
                self.refresh_tab_data("home")
        elif self.active_modal == "google":
            result = self.google_modal.update()
            self.google_modal.draw(self.screen)
            if result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.save_login()
                self.navbar.set_admin_mode(False)  # Social login = doctor
                self.refresh_tab_data("home")

    def handle_event(self, event):
        # Handle modal events first
        if self.active_modal == "apple":
            result = self.apple_modal.handle_event(event)
            if result == "cancel":
                self.active_modal = None
                self.apple_modal.reset()
            elif result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.save_login()
                self.navbar.set_admin_mode(False)
                self.refresh_tab_data("home")
            return

        if self.active_modal == "google":
            result = self.google_modal.handle_event(event)
            if result == "cancel":
                self.active_modal = None
                self.google_modal.reset()
            elif result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.save_login()
                self.navbar.set_admin_mode(False)
                self.refresh_tab_data("home")
            return

        if self.show_navbar:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.navbar.handle_click(event.pos):
                    return

            tab_name = self.navbar.get_selected_tab_name()
            if tab_name in self.tab_screens:
                result = self.tab_screens[tab_name].handle_event(event)
                if result == "close":
                    self.close()
                elif result == "logout":
                    self.logout()
                elif result == "refresh":
                    self.refresh_tab_data(tab_name)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.close()
            return

        current = self.screens[self.current_screen]
        result = current.handle_event(event)

        if result:
            self.handle_screen_result(result)

    def handle_screen_result(self, result):
        if result == "close":
            self.close()
        elif result == "signup_accepted":
            self.screens["signup"].terms_accepted = True
            self.current_screen = "signup"
        elif result == "apple_signin":
            self.apple_modal.reset()
            self.active_modal = "apple"
        elif result == "google_signin":
            self.google_modal.reset()
            self.active_modal = "google"
        elif result == "admin_main":
            # Full admin access - 5 tab navbar
            self.show_navbar = True
            self.user_role = "admin"
            self.current_doctor = None  # Admin is not a doctor
            self.navbar.set_admin_mode(True)  # Show all 5 tabs
            self.refresh_tab_data("home")
        elif result == "doctor_main":
            # Doctor access - 3 tab navbar (home, appointments, patients)
            self.show_navbar = True
            self.user_role = "doctor"
            self.current_doctor = self.db.get_current_doctor()
            self.navbar.set_admin_mode(False)  # Show only 3 tabs
            self.refresh_tab_data("home")
        elif result == "main":
            # Legacy support
            self.show_navbar = True
            self.user_role = "doctor"
            self.current_doctor = self.db.get_current_doctor()
            self.navbar.set_admin_mode(False)
            self.refresh_tab_data("home")
        elif result == "logout":
            self.logout()
        elif result in self.screens:
            target_screen = self.screens[result]
            if hasattr(target_screen, 'reset_swipe'):
                target_screen.reset_swipe()
            if hasattr(target_screen, 'ignore_next_mouseup'):
                target_screen.ignore_next_mouseup = True
            self.current_screen = result

    def update(self):
        if self.show_navbar:
            tab_name = self.navbar.get_selected_tab_name()
            if tab_name in self.tab_screens:
                current = self.tab_screens[tab_name]
                if hasattr(current, 'update'):
                    current.update()