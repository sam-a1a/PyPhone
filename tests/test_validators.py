"""Tests for the input validators used by the signup and admin forms."""
import pytest

from apps.shared.validators import Validators


class TestEmail:

    @pytest.mark.parametrize("email", [
        "user@example.com",
        "first.last@example.co.uk",
        "user+tag@example.com",
        "user_name@sub.example.com",
        "u@e.io",
        "123@456.com",
    ])
    def test_accepts_valid_addresses(self, email):
        assert Validators.validate_email(email) == (True, None)

    @pytest.mark.parametrize("email", [
        "no-at-sign.com",
        "@example.com",
        "user@",
        "user@example",          # no TLD
        "user@example.c",        # one-letter TLD
        "user name@example.com", # space
        "user@@example.com",
    ])
    def test_rejects_invalid_addresses(self, email):
        valid, message = Validators.validate_email(email)
        assert valid is False
        assert message

    @pytest.mark.parametrize("empty", ["", None])
    def test_email_is_required(self, empty):
        assert Validators.validate_email(empty) == (False, "Email is required")


class TestPhone:

    @pytest.mark.parametrize("phone", [
        "1234567890",
        "+11234567890",
        "+963956789012",
        "123 456 7890",
        "123-456-7890",
        "(123) 456-7890",
    ])
    def test_accepts_valid_numbers(self, phone):
        assert Validators.validate_phone(phone) == (True, None)

    @pytest.mark.parametrize("phone", [
        "123456789",          # too short
        "1234567890123456",   # too long
        "12345abcde",
        "++1234567890",
    ])
    def test_rejects_invalid_numbers(self, phone):
        valid, message = Validators.validate_phone(phone)
        assert valid is False
        assert message

    @pytest.mark.parametrize("empty", ["", None])
    def test_phone_is_required(self, empty):
        assert Validators.validate_phone(empty) == (False, "Phone number is required")


class TestName:

    @pytest.mark.parametrize("name", [
        "Ann", "Ann Lee", "Mary-Jane Watson", "Dr Alice Stone", "Al",
    ])
    def test_accepts_valid_names(self, name):
        assert Validators.validate_name(name) == (True, None)

    def test_rejects_a_single_character(self):
        valid, message = Validators.validate_name("A")
        assert valid is False
        assert "at least 2" in message

    @pytest.mark.parametrize("name", ["Ann3", "O'Brien", "Ann!", "Ann@Lee"])
    def test_rejects_names_with_disallowed_characters(self, name):
        valid, message = Validators.validate_name(name)
        assert valid is False
        assert "letters" in message

    def test_rejects_a_name_over_fifty_characters(self):
        assert Validators.validate_name("A" * 51)[0] is False

    @pytest.mark.parametrize("empty", ["", None])
    def test_name_is_required(self, empty):
        assert Validators.validate_name(empty) == (False, "Name is required")


class TestAge:

    @pytest.mark.parametrize("age", [0, 1, 35, 150, "42"])
    def test_accepts_ages_in_range(self, age):
        assert Validators.validate_age(age) == (True, None)

    @pytest.mark.parametrize("age", [-1, 151, 1000])
    def test_rejects_ages_out_of_range(self, age):
        valid, message = Validators.validate_age(age)
        assert valid is False
        assert "0-150" in message

    @pytest.mark.parametrize("age", ["", None, "abc", "3.5", []])
    def test_rejects_non_numbers(self, age):
        valid, message = Validators.validate_age(age)
        assert valid is False
        assert message == "Age must be a number"


class TestPassword:

    @pytest.mark.parametrize("password", ["12345678", "a much longer password", "        "])
    def test_accepts_eight_characters_or_more(self, password):
        assert Validators.validate_password(password) == (True, None)

    @pytest.mark.parametrize("password", ["1234567", "short", "a"])
    def test_rejects_anything_shorter(self, password):
        valid, message = Validators.validate_password(password)
        assert valid is False
        assert "at least 8" in message

    @pytest.mark.parametrize("empty", ["", None])
    def test_password_is_required(self, empty):
        assert Validators.validate_password(empty) == (False, "Password is required")

    def test_length_is_the_only_rule(self):
        # Worth stating plainly: no complexity requirement is enforced
        assert Validators.validate_password("aaaaaaaa") == (True, None)


class TestRequired:

    @pytest.mark.parametrize("value", ["x", "some text", ["item"], 1])
    def test_accepts_present_values(self, value):
        assert Validators.validate_required(value, "Field") == (True, None)

    @pytest.mark.parametrize("value", ["", "   ", "\t\n", None, []])
    def test_rejects_missing_or_blank_values(self, value):
        valid, message = Validators.validate_required(value, "Specialty")
        assert valid is False
        assert message == "Specialty is required"

    @pytest.mark.parametrize("value", [0, 0.0, False])
    def test_falsy_numbers_read_as_missing(self, value):
        # The check is `not value`, so a real zero is reported as missing.
        # Fine for the text fields it is used on; do not reach for it to
        # validate an age or a fee.
        assert Validators.validate_required(value, "Fee")[0] is False
