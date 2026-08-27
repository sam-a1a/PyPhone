"""Tests for the dataclass models and their dict round-trips."""
from datetime import datetime

import pytest

from apps.shared.models import (
    DISEASES, SPECIALTIES, Admin, Appointment, Doctor, Patient, Person,
)


class TestPerson:

    def test_defaults(self):
        person = Person()
        assert person.id is None
        assert person.name == ""
        assert person.age == 0

    def test_created_at_defaults_to_now(self):
        before = datetime.now()
        person = Person(name="Someone")
        assert before <= person.created_at <= datetime.now()

    def test_explicit_created_at_is_kept(self):
        stamp = datetime(2020, 1, 1, 12, 0)
        assert Person(created_at=stamp).created_at == stamp

    def test_to_dict(self):
        stamp = datetime(2020, 1, 1, 12, 0)
        data = Person(id=1, name="Ann", email="ann@x.test", phone="123",
                      age=30, created_at=stamp).to_dict()
        assert data == {
            "id": 1, "name": "Ann", "email": "ann@x.test", "phone": "123",
            "age": 30, "created_at": stamp.isoformat(),
        }

    def test_to_dict_with_no_timestamp(self):
        person = Person(name="Ann")
        person.created_at = None
        assert person.to_dict()["created_at"] is None

    def test_from_dict_round_trip(self):
        original = Person(id=2, name="Bo", email="bo@x.test", phone="9", age=44)
        restored = Person.from_dict(original.to_dict())
        assert restored == original

    def test_from_dict_parses_an_iso_timestamp(self):
        restored = Person.from_dict({"name": "Cy", "created_at": "2021-06-01T08:30:00"})
        assert restored.created_at == datetime(2021, 6, 1, 8, 30)


class TestPatient:

    def test_inherits_from_person(self):
        assert issubclass(Patient, Person)

    def test_defaults(self):
        pat = Patient()
        assert pat.patient_number == ""
        assert pat.assigned_doctor_id is None

    def test_to_dict_includes_patient_fields(self):
        data = Patient(name="Dee", patient_number="PAT9", disease="Flu",
                       assigned_doctor_id=3, medical_history="none").to_dict()
        assert data["patient_number"] == "PAT9"
        assert data["disease"] == "Flu"
        assert data["assigned_doctor_id"] == 3
        assert data["medical_history"] == "none"
        assert data["name"] == "Dee"  # and the inherited ones

    def test_from_dict_round_trip(self):
        original = Patient(id=5, name="Dee", email="d@x.test", disease="Flu")
        assert Patient.from_dict(original.to_dict()) == original


class TestDoctor:

    def test_inherits_from_person(self):
        assert issubclass(Doctor, Person)

    def test_scheduling_defaults(self):
        doc = Doctor()
        assert doc.is_active is True
        assert doc.max_patients == 20
        assert doc.available_days == "Mon,Tue,Wed,Thu,Fri"
        assert doc.available_hours == "09:00-17:00"

    def test_to_dict_includes_doctor_fields(self):
        data = Doctor(name="Dr. E", specialty="Neurology", consultation_fee=99.5).to_dict()
        assert data["specialty"] == "Neurology"
        assert data["consultation_fee"] == 99.5
        assert data["is_active"] is True

    def test_to_dict_exposes_the_password_hash(self):
        # Documented, not endorsed: to_dict feeds internal code only, never a
        # response body. Admin.to_dict deliberately omits it.
        assert "password_hash" in Doctor(password_hash="$2b$12$x").to_dict()

    def test_from_dict_round_trip(self):
        original = Doctor(id=7, name="Dr. F", email="f@x.test", specialty="ENT")
        assert Doctor.from_dict(original.to_dict()) == original


class TestAdmin:

    def test_defaults(self):
        adm = Admin()
        assert adm.is_active is True
        assert adm.password_hash == ""

    def test_created_at_defaults_to_now(self):
        assert Admin(name="Root").created_at is not None

    def test_to_dict_never_leaks_the_password_hash(self):
        data = Admin(name="Root", email="r@x.test", password_hash="$2b$12$secret").to_dict()
        assert "password_hash" not in data
        assert data["email"] == "r@x.test"


class TestAppointment:

    def test_defaults(self):
        appt = Appointment()
        assert appt.status == "scheduled"
        assert appt.appointment_date is None
        assert appt.created_at is not None

    def test_joined_fields_default_to_empty(self):
        appt = Appointment()
        assert appt.patient_name == ""
        assert appt.doctor_name == ""
        assert appt.doctor_specialty == ""

    def test_to_dict(self):
        when = datetime(2025, 3, 4, 9, 0)
        data = Appointment(id=1, patient_id=2, doctor_id=3, appointment_date=when,
                           appointment_time="09:00", notes="check-up").to_dict()
        assert data["appointment_date"] == when.isoformat()
        assert data["appointment_time"] == "09:00"
        assert data["status"] == "scheduled"

    def test_to_dict_with_no_date(self):
        assert Appointment(patient_id=1, doctor_id=1).to_dict()["appointment_date"] is None

    def test_to_dict_omits_joined_display_fields(self):
        appt = Appointment(patient_id=1, doctor_id=1)
        appt.patient_name = "Bob"
        assert "patient_name" not in appt.to_dict()


class TestReferenceData:

    def test_specialties_are_unique_and_non_empty(self):
        assert len(SPECIALTIES) == len(set(SPECIALTIES))
        assert all(s.strip() for s in SPECIALTIES)

    def test_diseases_are_unique_and_non_empty(self):
        assert len(DISEASES) == len(set(DISEASES))
        assert all(d.strip() for d in DISEASES)

    def test_general_practice_is_the_first_specialty(self):
        # Screens use SPECIALTIES[0] as the default selection
        assert SPECIALTIES[0] == "General Practice"
