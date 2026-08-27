"""The signup path end to end: form, code, account.

Covers the account-creation helpers on Database, the verify screen, and the
two apps' signup and login screens driven with synthetic pygame events.
"""
import pygame
import pytest

from apps.shared.models import Patient
from apps.shared.verification import CODE_LENGTH, MAX_ATTEMPTS, verification
from apps.verify_screen import VerifyScreen


def key_event(char):
    return pygame.event.Event(pygame.KEYDOWN, key=ord(char), unicode=char)


def type_code(screen, code):
    result = None
    for char in code:
        result = screen.handle_event(key_event(char))
    return result


class TestRegistrationHelpers:

    def test_registering_a_patient_returns_an_id(self, db):
        assert db.register_patient("Sam Tester", "sam@test.com", "supersecret") == 1

    def test_a_registered_patient_can_log_in(self, db):
        db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        assert db.authenticate_patient("sam@test.com", "supersecret") is not None

    def test_the_wrong_password_is_rejected(self, db):
        db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        assert db.authenticate_patient("sam@test.com", "supersecre") is None

    def test_the_password_is_stored_hashed(self, db):
        patient_id = db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        conn = db.get_connection()
        stored = conn.execute("SELECT password_hash FROM patients WHERE id = ?",
                              (patient_id,)).fetchone()["password_hash"]
        conn.close()
        assert stored.startswith("$2b$")
        assert "supersecret" not in stored

    def test_a_patient_number_is_assigned(self, db):
        patient_id = db.register_patient("Sam Tester", "sam@test.com", "supersecret")
        assert db.get_patient(patient_id).patient_number == "PAT001"

    def test_patient_numbers_increment(self, db):
        db.register_patient("One", "one@test.com", "password1")
        second = db.register_patient("Two", "two@test.com", "password2")
        assert db.get_patient(second).patient_number == "PAT002"

    def test_numbering_does_not_reuse_after_a_deletion(self, db):
        # Counting rows would hand out PAT001 twice, and the column is UNIQUE
        first = db.register_patient("One", "one@test.com", "password1")
        db.register_patient("Two", "two@test.com", "password2")
        db.delete_patient(first)
        third = db.register_patient("Three", "three@test.com", "password3")
        assert db.get_patient(third).patient_number == "PAT003"

    def test_numbering_ignores_unparseable_existing_numbers(self, db):
        pat = Patient(name="Legacy", email="legacy@test.com", patient_number="PAT-OLD")
        db.add_patient(pat)
        assert db.next_patient_number() == "PAT001"

    def test_registering_a_doctor(self, db):
        doctor_id = db.register_doctor("Dr. Alice", "alice@test.com", "doctorpass", "Cardiology")
        doctor = db.get_doctor(doctor_id)
        assert doctor.doctor_number == "DOC001"
        assert doctor.specialty == "Cardiology"
        assert db.authenticate_doctor("alice@test.com", "doctorpass") is not None

    def test_registering_an_admin(self, db):
        admin_id = db.register_admin("Root", "root@test.com", "adminpass1")
        assert db.get_admin(admin_id).name == "Root"
        assert db.authenticate_admin("root@test.com", "adminpass1") is not None

    def test_names_and_emails_are_trimmed(self, db):
        patient_id = db.register_patient("  Sam Tester  ", "  sam@test.com  ", "supersecret")
        patient = db.get_patient(patient_id)
        assert patient.name == "Sam Tester"
        assert patient.email == "sam@test.com"


class TestEmailUniqueness:

    def test_the_same_email_cannot_register_twice(self, db):
        db.register_patient("First", "taken@test.com", "password1")
        assert db.register_patient("Second", "taken@test.com", "password2") is None

    def test_an_email_is_unique_across_account_types(self, db):
        db.register_patient("Patient", "shared@test.com", "password1")
        assert db.register_doctor("Doctor", "shared@test.com", "password2", "ENT") is None
        assert db.register_admin("Admin", "shared@test.com", "password3") is None

    def test_email_taken_reports_each_type(self, db):
        db.register_patient("P", "p@test.com", "password1")
        db.register_doctor("D", "d@test.com", "password2", "ENT")
        db.register_admin("A", "a@test.com", "password3")
        assert db.email_taken("p@test.com") is True
        assert db.email_taken("d@test.com") is True
        assert db.email_taken("a@test.com") is True

    def test_an_unused_email_is_free(self, db):
        assert db.email_taken("nobody@test.com") is False

    @pytest.mark.parametrize("value", ["", None, "   "])
    def test_a_blank_email_is_not_reported_as_taken(self, db, value):
        assert db.email_taken(value) is False

    def test_a_failed_registration_writes_nothing(self, db):
        db.register_patient("First", "taken@test.com", "password1")
        db.register_patient("Second", "taken@test.com", "password2")
        assert len(db.get_all_patients()) == 1


class TestVerifyScreen:

    @pytest.fixture
    def screen(self, db):
        verify = VerifyScreen(service=verification)
        verification.send_code("sam@test.com")
        verify.start("sam@test.com")
        return verify

    def test_it_starts_empty(self, screen):
        assert screen.digits == ""
        assert screen.is_complete is False

    def test_typing_fills_the_boxes(self, screen):
        screen.handle_event(key_event("1"))
        screen.handle_event(key_event("2"))
        assert screen.digits == "12"

    def test_non_digits_are_ignored(self, screen):
        screen.handle_event(key_event("a"))
        screen.handle_event(key_event("!"))
        assert screen.digits == ""

    def test_backspace_removes_a_digit(self, screen):
        screen.handle_event(key_event("1"))
        screen.handle_event(key_event("2"))
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode=""))
        assert screen.digits == "1"

    def test_it_stops_at_the_code_length(self, screen):
        type_code(screen, "1234567890")
        assert len(screen.digits) <= CODE_LENGTH

    def test_the_right_code_verifies(self, screen):
        assert type_code(screen, verification.peek_code("sam@test.com")) == "verified"

    def test_filling_the_last_box_submits_on_its_own(self, screen):
        code = verification.peek_code("sam@test.com")
        assert type_code(screen, code) == "verified"

    def test_a_wrong_code_reports_an_error(self, screen):
        code = verification.peek_code("sam@test.com")
        wrong = "000000" if code != "000000" else "111111"
        assert type_code(screen, wrong) is None
        assert screen.error is not None

    def test_a_wrong_code_clears_the_boxes_to_retry(self, screen):
        code = verification.peek_code("sam@test.com")
        type_code(screen, "000000" if code != "000000" else "111111")
        assert screen.digits == ""

    def test_typing_again_clears_the_error(self, screen):
        code = verification.peek_code("sam@test.com")
        type_code(screen, "000000" if code != "000000" else "111111")
        screen.handle_event(key_event("1"))
        assert screen.error is None

    def test_submitting_a_partial_code_complains(self, screen):
        screen.handle_event(key_event("1"))
        assert screen.submit() is None
        assert "digits" in screen.error

    def test_enter_submits(self, screen):
        code = verification.peek_code("sam@test.com")
        for char in code[:-1]:
            screen.handle_event(key_event(char))
        screen.digits = code
        result = screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
        assert result == "verified"

    def test_escape_goes_back(self, screen):
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="")
        assert screen.handle_event(event) == "signup"

    def test_running_out_of_attempts_is_reported(self, screen):
        code = verification.peek_code("sam@test.com")
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(MAX_ATTEMPTS):
            type_code(screen, wrong)
        assert "Too many" in screen.error

    def test_starting_again_clears_previous_state(self, screen):
        screen.handle_event(key_event("1"))
        screen.error = "stale"
        screen.start("other@test.com")
        assert screen.digits == ""
        assert screen.error is None
        assert screen.email == "other@test.com"

    def test_it_draws(self, screen):
        surface = pygame.Surface((420, 850))
        screen.draw(surface)

    def test_it_draws_with_an_error_showing(self, screen):
        screen.error = "That code is not right"
        screen.draw(pygame.Surface((420, 850)))

    def test_resending_is_rate_limited(self, screen):
        screen.request_resend()
        assert "Wait" in screen.resend_notice

    def test_a_resend_request_is_reported_once(self, screen, monkeypatch):
        monkeypatch.setattr(screen.service, "can_resend", lambda email: True)
        screen.request_resend()
        assert screen.take_resend_request() is True
        assert screen.take_resend_request() is False

    def test_resending_issues_a_different_code(self, screen, monkeypatch):
        monkeypatch.setattr(screen.service, "can_resend", lambda email: True)
        first = verification.peek_code("sam@test.com")
        screen.request_resend()
        assert verification.peek_code("sam@test.com") != first


class TestVerifyScreenClicks:
    """The mouse paths through the verify screen."""

    @pytest.fixture
    def screen(self, db):
        verify = VerifyScreen(service=verification)
        verification.send_code("sam@test.com")
        verify.start("sam@test.com")
        verify.draw(pygame.Surface((420, 850)))   # lays out the click targets
        return verify

    @staticmethod
    def click(pos):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)

    def test_back_returns_to_signup(self, screen):
        assert screen.handle_event(self.click(screen.back_rect.center)) == "signup"

    def test_the_verify_button_submits(self, screen):
        screen.digits = verification.peek_code("sam@test.com")
        result = screen.handle_event(self.click((210, screen.button_y + 25)))
        assert result == "verified"

    def test_the_verify_button_complains_when_incomplete(self, screen):
        screen.handle_event(self.click((210, screen.button_y + 25)))
        assert "digits" in screen.error

    def test_a_click_beside_the_button_does_nothing(self, screen):
        assert screen.handle_event(self.click((5, screen.button_y + 25))) is None

    def test_the_resend_link_is_clickable(self, screen):
        screen.handle_event(self.click(screen.resend_rect.center))
        assert screen.resend_notice is not None

    def test_a_click_on_empty_space_does_nothing(self, screen):
        assert screen.handle_event(self.click((210, 780))) is None

    def test_it_draws_the_digits_already_typed(self, screen):
        screen.digits = "123"
        screen.draw(pygame.Surface((420, 850)))
        assert screen.digits == "123"

    def test_it_draws_a_resend_notice(self, screen):
        screen.request_resend()
        screen.draw(pygame.Surface((420, 850)))
        assert screen.resend_notice is not None

    def test_it_draws_a_full_code(self, screen):
        screen.digits = "123456"
        screen.draw(pygame.Surface((420, 850)))
        assert screen.is_complete is True

    def test_a_custom_back_target_is_honoured(self, db):
        verify = VerifyScreen(service=verification, back_target="onboarding")
        verify.draw(pygame.Surface((420, 850)))
        assert verify.handle_event(self.click(verify.back_rect.center)) == "onboarding"


class TestAttemptLimitBurnsAnOutstandingCode:

    def test_a_code_already_at_the_limit_is_reported_and_dropped(self, db):
        # Reaching the cap on one call and then verifying again takes the
        # second branch, where the code is found already spent
        from apps.shared.verification import (
            MAX_ATTEMPTS as LIMIT, TOO_MANY_ATTEMPTS as LIMIT_HIT, VerificationService,
        )
        service = VerificationService()
        code = service.send_code("burn@test.com")
        wrong = "000000" if code != "000000" else "111111"
        service._pending["burn@test.com"].attempts = LIMIT
        assert service.verify("burn@test.com", wrong) == LIMIT_HIT
