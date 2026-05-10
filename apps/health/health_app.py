import pygame
from apps.base_app import BaseApp
from apps.health.components import BottomNavbar
from apps.health.screens import (
    OnboardingScreen,
    LoginScreen,
    SignupScreen,
    TermsScreen,
    MainScreen,
    ForgotPasswordScreen,
    AppleSignInModal,
    GoogleSignInModal,
    BookScreen,
    HistoryScreen,
    MapScreen
)
from apps.shared import Database
from components import draw_status_bar

class HealthApp(BaseApp):

    def __init__(self, screen):
        super().__init__(screen)
        self.app_name = "Health"
        self.db = Database()

        self.screens = {
            "onboarding": OnboardingScreen(),
            "login": LoginScreen(),
            "signup": SignupScreen(),
            "terms": TermsScreen(),
            "main": MainScreen(),
            "forgot_password": ForgotPasswordScreen()
        }

        if self.db.is_logged_in():
            self.current_screen = "main"
            self.show_navbar = True
        else:
            self.current_screen = "onboarding"
            self.show_navbar = False

        self.tab_screens = {
            "home": MainScreen(),
            "book": BookScreen(),
            "history": HistoryScreen(),
            "map": MapScreen()
        }

        self.navbar = BottomNavbar()
        self.last_tab = None

        self.apple_modal = AppleSignInModal()
        self.google_modal = GoogleSignInModal()
        self.active_modal = None

    def refresh_tab_data(self, tab_name):
        if tab_name == "history":
            self.tab_screens["history"].load_appointments()
        elif tab_name == "home":
            pass
        elif tab_name == "book":
            self.tab_screens["book"].load_doctors()

    def save_login(self):
        self.db.save_session("patient", 1, "demo@patient.com")

    def logout(self):
        self.db.clear_session()
        self.show_navbar = False
        self.current_screen = "onboarding"

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
        elif self.active_modal == "google":
            result = self.google_modal.update()
            self.google_modal.draw(self.screen)
            if result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.save_login()

    def handle_event(self, event):
        if self.active_modal == "apple":
            result = self.apple_modal.handle_event(event)
            if result == "cancel":
                self.active_modal = None
                self.apple_modal.reset()
            elif result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.save_login()
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

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.close()
            return

        current = self.screens[self.current_screen]
        result = current.handle_event(event)

        if result:
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
            elif result == "main":
                self.show_navbar = True
                self.save_login()
            elif result in self.screens:
                target_screen = self.screens[result]
                if hasattr(target_screen, 'reset_swipe'):
                    target_screen.reset_swipe()
                if hasattr(target_screen, 'ignore_next_mouseup'):
                    target_screen.ignore_next_mouseup = True
                self.current_screen = result