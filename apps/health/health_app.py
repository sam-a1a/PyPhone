import pygame
import secrets
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
from apps.shared.verification import verification
from apps.verify_screen import VerifyScreen
from components import draw_status_bar
from components.notification import NotificationBanner

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
            "forgot_password": ForgotPasswordScreen(),
            "verify": VerifyScreen(app_name="Health", accent=(0, 122, 255),
                                   back_target="signup"),
        }

        # The code is delivered the way a real one would be: as a notification
        self.notification = NotificationBanner()

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

    def notify_code(self, email):
        #Show the verification code as a system notification banner
        code = verification.peek_code(email)
        if code is None:
            return
        self.notification.show(
            "Health", "Verification code",
            f"{code} is your Health verification code.",
            icon_name="health",
        )

    def start_verification(self):
        #Move to the code screen after a signup form has been submitted
        pending = self.screens["signup"].pending_signup
        if not pending:
            return
        self.screens["verify"].start(pending["email"])
        self.current_screen = "verify"
        self.notify_code(pending["email"])

    def complete_signup(self):
        #The code checked out, so the account can finally be created
        pending = self.screens["signup"].pending_signup
        if not pending:
            return
        patient_id = self.db.register_patient(
            name=pending["name"], email=pending["email"], password=pending["password"]
        )
        if patient_id is None:
            # Someone claimed the address between form and code
            self.screens["signup"].form_error = "That email already has an account"
            self.current_screen = "signup"
            return
        self.db.save_session("patient", patient_id, pending["email"])
        self.screens["signup"].reset()
        self.show_navbar = True
        self.refresh_tab_data("home")

    def apple_login(self):
        self.social_login(self.apple_modal.user_email, "Apple User")

    def google_login(self):
        index = self.google_modal.selected_account
        account = self.google_modal.accounts[index if index is not None else 0]
        self.social_login(account["email"], account["name"])

    def social_login(self, email, name):
        #Apple and Google sign-in: reuse the account if it exists, else make one
        patient = self.db.get_patient_by_email(email)
        if patient is None:
            patient_id = self.db.register_patient(
                name=name, email=email, password=secrets.token_urlsafe(32)
            )
            if patient_id is None:
                return
        else:
            patient_id = patient.id
        self.db.save_session("patient", patient_id, email)
        self.refresh_tab_data("home")

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
                self.apple_login()
        elif self.active_modal == "google":
            result = self.google_modal.update()
            self.google_modal.draw(self.screen)
            if result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.google_login()

        self.notification.update()
        self.notification.draw(self.screen)

    def handle_event(self, event):
        # A tap on the banner dismisses it rather than reaching the screen below
        if self.notification.handle_event(event):
            return

        if self.active_modal == "apple":
            result = self.apple_modal.handle_event(event)
            if result == "cancel":
                self.active_modal = None
                self.apple_modal.reset()
            elif result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.apple_login()
            return

        if self.active_modal == "google":
            result = self.google_modal.handle_event(event)
            if result == "cancel":
                self.active_modal = None
                self.google_modal.reset()
            elif result == "complete":
                self.active_modal = None
                self.show_navbar = True
                self.google_login()
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

        if self.current_screen == "verify" and self.screens["verify"].take_resend_request():
            self.notify_code(self.screens["verify"].email)

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
            elif result == "verify":
                self.start_verification()
            elif result == "verified":
                self.complete_signup()
            elif result == "main":
                self.show_navbar = True
                self.refresh_tab_data("home")
            elif result in self.screens:
                target_screen = self.screens[result]
                if hasattr(target_screen, 'reset_swipe'):
                    target_screen.reset_swipe()
                if hasattr(target_screen, 'ignore_next_mouseup'):
                    target_screen.ignore_next_mouseup = True
                self.current_screen = result