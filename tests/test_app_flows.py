"""Signup and login driven through the apps themselves.

These build the real HealthApp / HealthAdminApp against a temp database and
push events through them, so the screen wiring is covered, not just the
database layer underneath it.
"""
import pygame
import pytest

from apps.shared.verification import verification


@pytest.fixture
def surface():
    return pygame.Surface((420, 850))


@pytest.fixture
def health_app(db, surface):
    from apps.health.health_app import HealthApp
    return HealthApp(surface)


@pytest.fixture
def admin_app(db, surface):
    from apps.health_admin.health_admin_app import HealthAdminApp
    return HealthAdminApp(surface)


def key_event(char):
    return pygame.event.Event(pygame.KEYDOWN, key=ord(char), unicode=char)


def enter_code(verify_screen, code):
    result = None
    for char in code:
        result = verify_screen.handle_event(key_event(char))
    return result


class TestPatientSignup:

    @staticmethod
    def fill(app, name="Sam Tester", email="sam@test.com", password="supersecret",
             terms=True):
        signup = app.screens["signup"]
        signup.name_text = name
        signup.email_text = email
        signup.password_text = password
        signup.terms_accepted = terms
        return signup

    def test_a_valid_form_asks_for_a_code(self, health_app):
        assert self.fill(health_app).attempt_signup() == "verify"

    def test_no_account_exists_before_the_code_is_confirmed(self, health_app, db):
        self.fill(health_app).attempt_signup()
        assert db.get_patient_by_email("sam@test.com") is None

    def test_an_incomplete_form_is_refused(self, health_app):
        assert self.fill(health_app, name="").attempt_signup() is None

    def test_the_terms_must_be_accepted(self, health_app):
        signup = self.fill(health_app, terms=False)
        assert signup.attempt_signup() is None
        assert "Terms" in signup.form_error

    def test_a_taken_email_is_refused(self, health_app, db):
        db.register_patient("Existing", "sam@test.com", "password1")
        signup = self.fill(health_app)
        assert signup.attempt_signup() is None
        assert "already has an account" in signup.form_error

    def test_starting_verification_shows_the_notification(self, health_app):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        assert health_app.notification.visible is True
        assert health_app.current_screen == "verify"

    def test_the_notification_carries_the_code(self, health_app):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        code = verification.peek_code("sam@test.com")
        assert code in health_app.notification.body

    def test_the_notification_is_from_the_health_app(self, health_app):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        assert health_app.notification.app_name == "HEALTH"

    def test_the_right_code_creates_the_account(self, health_app, db):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        code = verification.peek_code("sam@test.com")
        assert enter_code(health_app.screens["verify"], code) == "verified"
        health_app.complete_signup()
        patient = db.get_patient_by_email("sam@test.com")
        assert patient is not None
        assert patient.name == "Sam Tester"

    def test_the_new_account_is_signed_in(self, health_app, db):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        enter_code(health_app.screens["verify"], verification.peek_code("sam@test.com"))
        health_app.complete_signup()
        assert db.get_current_user_type() == "patient"
        assert health_app.show_navbar is True

    def test_the_new_password_works_for_logging_in(self, health_app, db):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        enter_code(health_app.screens["verify"], verification.peek_code("sam@test.com"))
        health_app.complete_signup()
        assert db.authenticate_patient("sam@test.com", "supersecret") is not None

    def test_a_wrong_code_creates_nothing(self, health_app, db):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        code = verification.peek_code("sam@test.com")
        enter_code(health_app.screens["verify"], "000000" if code != "000000" else "111111")
        assert db.get_patient_by_email("sam@test.com") is None
        assert db.is_logged_in() is False

    def test_the_form_is_cleared_after_signing_up(self, health_app):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        enter_code(health_app.screens["verify"], verification.peek_code("sam@test.com"))
        health_app.complete_signup()
        assert health_app.screens["signup"].email_text == ""

    def test_an_email_claimed_mid_flow_sends_the_user_back(self, health_app, db):
        self.fill(health_app).attempt_signup()
        health_app.start_verification()
        db.register_patient("Faster", "sam@test.com", "password1")
        enter_code(health_app.screens["verify"], verification.peek_code("sam@test.com"))
        health_app.complete_signup()
        assert health_app.current_screen == "signup"
        assert "already has an account" in health_app.screens["signup"].form_error

    def test_completing_without_a_pending_signup_is_harmless(self, health_app, db):
        health_app.complete_signup()
        assert db.is_logged_in() is False


class TestPatientLogin:

    def test_a_registered_patient_can_sign_in(self, health_app, db):
        db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        login = health_app.screens["login"]
        login.email_text, login.password_text = "sam@test.com", "supersecret"
        assert login.attempt_login() == "main"
        assert db.get_current_user_type() == "patient"

    def test_the_wrong_password_is_refused(self, health_app, db):
        db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        login = health_app.screens["login"]
        login.email_text, login.password_text = "sam@test.com", "wrongpass"
        assert login.attempt_login() is None
        assert login.login_error == "Incorrect email or password"
        assert db.is_logged_in() is False

    def test_an_unknown_email_gives_the_same_message(self, health_app, db):
        # Saying "no such account" would confirm which addresses are registered
        login = health_app.screens["login"]
        login.email_text, login.password_text = "nobody@test.com", "supersecret"
        login.attempt_login()
        assert login.login_error == "Incorrect email or password"

    def test_a_failed_attempt_clears_the_password_field(self, health_app, db):
        db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        login = health_app.screens["login"]
        login.email_text, login.password_text = "sam@test.com", "wrongpass"
        login.attempt_login()
        assert login.password_text == ""

    def test_a_short_password_never_reaches_the_database(self, health_app, db):
        login = health_app.screens["login"]
        login.email_text, login.password_text = "sam@test.com", "short"
        assert login.attempt_login() is None

    def test_typing_clears_a_previous_error(self, health_app, db):
        login = health_app.screens["login"]
        login.email_text, login.password_text = "nobody@test.com", "supersecret"
        login.attempt_login()
        login.active_input = "email"
        login.handle_event(key_event("x"))
        assert login.login_error is None

    def test_logging_out_ends_the_session(self, health_app, db):
        db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        login = health_app.screens["login"]
        login.email_text, login.password_text = "sam@test.com", "supersecret"
        login.attempt_login()
        health_app.logout()
        assert db.is_logged_in() is False
        assert health_app.current_screen == "onboarding"


class TestDoctorAndAdminSignup:

    @staticmethod
    def fill(app, role, email="alice@hosp.test", specialty="Cardiology"):
        signup = app.screens["signup"]
        signup.reset()
        signup.name_text = "Alice Stone"
        signup.email_text = email
        signup.password_text = "doctorpass"
        signup.specialty_text = specialty
        signup.role = role
        signup.terms_accepted = True
        return signup

    def run_flow(self, app, role, email="alice@hosp.test", specialty="Cardiology"):
        self.fill(app, role, email, specialty).attempt_signup()
        app.start_verification()
        enter_code(app.screens["verify"], verification.peek_code(email))
        app.complete_signup()

    def test_the_default_role_is_doctor(self, admin_app):
        assert admin_app.screens["signup"].role == "doctor"

    def test_a_doctor_can_sign_up(self, admin_app, db):
        self.run_flow(admin_app, "doctor")
        doctor = db.get_doctor_by_email("alice@hosp.test")
        assert doctor is not None
        assert doctor.specialty == "Cardiology"
        assert doctor.doctor_number == "DOC001"

    def test_the_new_doctor_is_signed_in_as_a_doctor(self, admin_app, db):
        self.run_flow(admin_app, "doctor")
        assert db.get_current_user_type() == "doctor"
        assert admin_app.user_role == "doctor"

    def test_the_new_doctor_can_log_in(self, admin_app, db):
        self.run_flow(admin_app, "doctor")
        assert db.authenticate_doctor("alice@hosp.test", "doctorpass") is not None

    def test_an_administrator_can_sign_up(self, admin_app, db):
        self.run_flow(admin_app, "admin", email="root@hosp.test", specialty="")
        assert db.get_admin_by_email("root@hosp.test") is not None

    def test_the_new_administrator_is_signed_in_as_an_admin(self, admin_app, db):
        self.run_flow(admin_app, "admin", email="root@hosp.test", specialty="")
        assert db.get_current_user_type() == "admin"
        assert admin_app.user_role == "admin"

    def test_an_administrator_needs_no_specialty(self, admin_app):
        signup = self.fill(admin_app, "admin", specialty="")
        assert signup.is_form_valid() is True

    def test_a_doctor_does_need_a_specialty(self, admin_app):
        signup = self.fill(admin_app, "doctor", specialty="")
        assert signup.is_form_valid() is False

    def test_the_specialty_field_is_hidden_for_administrators(self, admin_app, surface):
        signup = self.fill(admin_app, "admin", specialty="")
        signup.draw(surface)
        assert signup.specialty_y is None

    def test_the_specialty_field_is_shown_for_doctors(self, admin_app, surface):
        signup = self.fill(admin_app, "doctor")
        signup.draw(surface)
        assert signup.specialty_y is not None

    def test_the_role_picker_switches_role(self, admin_app, surface):
        signup = self.fill(admin_app, "doctor")
        signup.draw(surface)
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                   pos=signup.role_rects["admin"].center, button=1)
        signup.handle_event(click)
        assert signup.role == "admin"

    def test_the_notification_is_from_the_admin_app(self, admin_app):
        self.fill(admin_app, "doctor").attempt_signup()
        admin_app.start_verification()
        assert admin_app.notification.app_name == "HEALTH ADMIN"
        assert verification.peek_code("alice@hosp.test") in admin_app.notification.body

    def test_a_wrong_code_creates_nothing(self, admin_app, db):
        self.fill(admin_app, "doctor").attempt_signup()
        admin_app.start_verification()
        code = verification.peek_code("alice@hosp.test")
        enter_code(admin_app.screens["verify"], "000000" if code != "000000" else "111111")
        assert db.get_doctor_by_email("alice@hosp.test") is None

    def test_a_taken_email_is_refused(self, admin_app, db):
        db.register_doctor("Existing", "alice@hosp.test", "password1", "ENT")
        signup = self.fill(admin_app, "doctor")
        assert signup.attempt_signup() is None
        assert "already has an account" in signup.form_error

    def test_two_doctors_get_different_numbers(self, admin_app, db):
        self.run_flow(admin_app, "doctor")
        admin_app.logout()
        self.run_flow(admin_app, "doctor", email="bob@hosp.test", specialty="ENT")
        assert db.get_doctor_by_email("bob@hosp.test").doctor_number == "DOC002"


class TestNoDemoAccounts:

    def test_the_health_app_starts_logged_out(self, health_app, db):
        assert db.is_logged_in() is False
        assert health_app.current_screen == "onboarding"
        assert health_app.show_navbar is False

    def test_the_admin_app_starts_logged_out(self, admin_app, db):
        assert db.is_logged_in() is False
        assert admin_app.current_screen == "onboarding"

    def test_the_old_demo_patient_login_no_longer_works(self, health_app, db):
        login = health_app.screens["login"]
        login.email_text, login.password_text = "demo@patient.com", "demo@patient.com"
        assert login.attempt_login() is None
        assert db.is_logged_in() is False
