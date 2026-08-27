"""Tests for the signup verification codes."""
import pytest

from apps.shared import verification as vmod
from apps.shared.verification import (
    CODE_LENGTH, EXPIRED, INCORRECT, MAX_ATTEMPTS, NO_CODE, OK,
    RESEND_COOLDOWN_SECONDS, TOO_MANY_ATTEMPTS, VerificationService,
    generate_code,
)


class FakeClock:
    """A clock the test moves by hand, so expiry needs no waiting."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def service(clock):
    return VerificationService(clock=clock)


class TestCodeGeneration:

    def test_code_is_the_right_length(self):
        assert len(generate_code()) == CODE_LENGTH

    def test_code_is_all_digits(self):
        assert generate_code().isdigit()

    def test_codes_vary(self):
        # 6 digits gives a million possibilities, so 50 draws colliding into
        # fewer than 40 distinct values would mean something is badly wrong
        assert len({generate_code() for _ in range(50)}) > 40

    def test_short_values_are_zero_padded(self, monkeypatch):
        monkeypatch.setattr(vmod.secrets, "randbelow", lambda n: 42)
        assert generate_code() == "000042"


class TestSendingCodes:

    def test_sending_returns_a_usable_code(self, service):
        code = service.send_code("a@test.com")
        assert len(code) == CODE_LENGTH
        assert service.verify("a@test.com", code) == OK

    def test_a_code_is_pending_after_sending(self, service):
        assert service.has_pending_code("a@test.com") is False
        service.send_code("a@test.com")
        assert service.has_pending_code("a@test.com") is True

    def test_peek_returns_the_outstanding_code(self, service):
        code = service.send_code("a@test.com")
        assert service.peek_code("a@test.com") == code

    def test_peek_with_nothing_outstanding(self, service):
        assert service.peek_code("nobody@test.com") is None

    def test_sending_again_replaces_the_previous_code(self, service):
        first = service.send_code("a@test.com")
        second = service.send_code("a@test.com")
        assert service.verify("a@test.com", first) == INCORRECT
        assert service.verify("a@test.com", second) == OK

    def test_codes_are_per_email(self, service):
        a_code = service.send_code("a@test.com")
        service.send_code("b@test.com")
        assert service.verify("b@test.com", a_code) == INCORRECT

    def test_email_matching_ignores_case_and_padding(self, service):
        code = service.send_code("Sam@Test.com")
        assert service.verify("  sam@test.com  ", code) == OK


class TestVerifying:

    def test_the_right_code_passes(self, service):
        code = service.send_code("a@test.com")
        assert service.verify("a@test.com", code) == OK

    def test_a_code_is_single_use(self, service):
        code = service.send_code("a@test.com")
        service.verify("a@test.com", code)
        assert service.verify("a@test.com", code) == NO_CODE

    def test_verifying_without_a_code_says_so(self, service):
        assert service.verify("nobody@test.com", "123456") == NO_CODE

    def test_a_wrong_code_is_rejected(self, service):
        code = service.send_code("a@test.com")
        wrong = "000000" if code != "000000" else "111111"
        assert service.verify("a@test.com", wrong) == INCORRECT

    @pytest.mark.parametrize("value", ["", None, "12345", "1234567", "abcdef"])
    def test_malformed_input_is_rejected_without_raising(self, service, value):
        service.send_code("a@test.com")
        assert service.verify("a@test.com", value) == INCORRECT

    def test_a_wrong_code_does_not_burn_the_right_one(self, service):
        code = service.send_code("a@test.com")
        service.verify("a@test.com", "000000" if code != "000000" else "111111")
        assert service.verify("a@test.com", code) == OK


class TestExpiry:

    def test_a_code_works_just_before_it_expires(self, service, clock):
        code = service.send_code("a@test.com")
        clock.advance(vmod.CODE_TTL_SECONDS - 1)
        assert service.verify("a@test.com", code) == OK

    def test_a_code_expires(self, service, clock):
        code = service.send_code("a@test.com")
        clock.advance(vmod.CODE_TTL_SECONDS + 1)
        assert service.verify("a@test.com", code) == EXPIRED

    def test_an_expired_code_is_discarded(self, service, clock):
        code = service.send_code("a@test.com")
        clock.advance(vmod.CODE_TTL_SECONDS + 1)
        service.verify("a@test.com", code)
        assert service.verify("a@test.com", code) == NO_CODE

    def test_a_fresh_code_after_expiry_works(self, service, clock):
        service.send_code("a@test.com")
        clock.advance(vmod.CODE_TTL_SECONDS + 1)
        new_code = service.send_code("a@test.com")
        assert service.verify("a@test.com", new_code) == OK


class TestAttemptLimit:

    @staticmethod
    def wrong_for(code):
        return "000000" if code != "000000" else "111111"

    def test_wrong_guesses_are_allowed_up_to_the_limit(self, service):
        code = service.send_code("a@test.com")
        wrong = self.wrong_for(code)
        for _ in range(MAX_ATTEMPTS - 1):
            assert service.verify("a@test.com", wrong) == INCORRECT

    def test_the_limit_burns_the_code(self, service):
        code = service.send_code("a@test.com")
        wrong = self.wrong_for(code)
        outcomes = [service.verify("a@test.com", wrong) for _ in range(MAX_ATTEMPTS)]
        assert outcomes[-1] == TOO_MANY_ATTEMPTS

    def test_the_right_code_no_longer_works_after_the_limit(self, service):
        code = service.send_code("a@test.com")
        wrong = self.wrong_for(code)
        for _ in range(MAX_ATTEMPTS):
            service.verify("a@test.com", wrong)
        assert service.verify("a@test.com", code) == NO_CODE

    def test_a_new_code_resets_the_attempt_count(self, service):
        code = service.send_code("a@test.com")
        wrong = self.wrong_for(code)
        for _ in range(MAX_ATTEMPTS - 1):
            service.verify("a@test.com", wrong)
        fresh = service.send_code("a@test.com")
        assert service.verify("a@test.com", fresh) == OK


class TestResendCooldown:

    def test_resending_immediately_is_blocked(self, service):
        service.send_code("a@test.com")
        assert service.can_resend("a@test.com") is False

    def test_the_wait_counts_down(self, service, clock):
        service.send_code("a@test.com")
        assert service.seconds_until_resend("a@test.com") == RESEND_COOLDOWN_SECONDS
        clock.advance(10)
        assert service.seconds_until_resend("a@test.com") == RESEND_COOLDOWN_SECONDS - 10

    def test_resending_is_allowed_after_the_cooldown(self, service, clock):
        service.send_code("a@test.com")
        clock.advance(RESEND_COOLDOWN_SECONDS)
        assert service.can_resend("a@test.com") is True

    def test_a_first_send_is_never_blocked(self, service):
        assert service.can_resend("brand-new@test.com") is True
        assert service.seconds_until_resend("brand-new@test.com") == 0


class TestClearing:

    def test_clearing_abandons_the_code(self, service):
        code = service.send_code("a@test.com")
        service.clear("a@test.com")
        assert service.verify("a@test.com", code) == NO_CODE

    def test_clearing_an_unknown_email_is_harmless(self, service):
        service.clear("nobody@test.com")

    def test_clear_all_empties_everything(self, service):
        service.send_code("a@test.com")
        service.send_code("b@test.com")
        service.clear_all()
        assert service.has_pending_code("a@test.com") is False
        assert service.has_pending_code("b@test.com") is False


def test_the_module_exposes_a_shared_service():
    # Screens import this one rather than each making their own
    assert isinstance(vmod.verification, VerificationService)
