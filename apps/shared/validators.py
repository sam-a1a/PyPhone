import re

class Validators:

    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^[\+]?[0-9]{10,15}$')
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-]{2,50}$')
    PASSWORD_PATTERN = re.compile(r'^.{8,}$')

    @staticmethod
    def validate_email(email):
        if not email:
            return False, "Email is required"
        if not Validators.EMAIL_PATTERN.match(email):
            return False, "Please enter a valid email address"
        return True, None

    @staticmethod
    def validate_phone(phone):
        if not phone:
            return False, "Phone number is required"
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not Validators.PHONE_PATTERN.match(clean_phone):
            return False, "Please enter a valid phone number"
        return True, None

    @staticmethod
    def validate_name(name):
        if not name:
            return False, "Name is required"
        if len(name.strip()) < 2:
            return False, "Name must be at least 2 characters"
        if not Validators.NAME_PATTERN.match(name):
            return False, "Name can only contain letters, spaces, and hyphens"
        return True, None

    @staticmethod
    def validate_age(age):
        try:
            age_int = int(age)
            if age_int < 0 or age_int > 150:
                return False, "Please enter a valid age (0-150)"
            return True, None
        except (ValueError, TypeError):
            return False, "Age must be a number"

    @staticmethod
    def validate_password(password):
        if not password:
            return False, "Password is required"
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        return True, None

    @staticmethod
    def validate_required(value, field_name):
        if not value or (isinstance(value, str) and not value.strip()):
            return False, f"{field_name} is required"
        return True, None