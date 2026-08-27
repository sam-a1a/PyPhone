"""Appointment booking, status changes and slot availability."""
from datetime import datetime, timedelta

import pytest

from apps.shared.models import Appointment


def book(db, doctor_id, patient_id, days_ahead=1, time="10:00", status="scheduled"):
    appt = Appointment(
        patient_id=patient_id, doctor_id=doctor_id,
        appointment_date=datetime.now() + timedelta(days=days_ahead),
        appointment_time=time, status=status,
    )
    appt.id = db.add_appointment(appt)
    return appt


class TestAddAndGet:

    def test_add_returns_a_new_id(self, empty_db, doctor, patient):
        assert book(empty_db, doctor.id, patient.id).id == 1

    def test_get_returns_the_stored_fields(self, empty_db, appointment):
        loaded = empty_db.get_appointment(appointment.id)
        assert loaded.appointment_time == "10:00"
        assert loaded.status == "scheduled"
        assert loaded.notes == "Follow-up"

    def test_get_joins_the_patient_and_doctor_names(self, empty_db, appointment):
        loaded = empty_db.get_appointment(appointment.id)
        assert loaded.patient_name == "Bob Reed"
        assert loaded.doctor_name == "Dr. Alice Stone"
        assert loaded.doctor_specialty == "Cardiology"

    def test_get_unknown_id_returns_none(self, empty_db):
        assert empty_db.get_appointment(9999) is None

    def test_the_date_round_trips_as_a_datetime(self, empty_db, appointment):
        assert isinstance(empty_db.get_appointment(appointment.id).appointment_date, datetime)

    def test_an_appointment_with_no_date_can_be_stored(self, empty_db, doctor, patient):
        appt = Appointment(patient_id=patient.id, doctor_id=doctor.id, appointment_time="09:00")
        appt_id = empty_db.add_appointment(appt)
        assert empty_db.get_appointment(appt_id).appointment_date is None

    def test_status_defaults_to_scheduled(self, empty_db, doctor, patient):
        appt = Appointment(patient_id=patient.id, doctor_id=doctor.id,
                           appointment_date=datetime.now())
        appt_id = empty_db.add_appointment(appt)
        assert empty_db.get_appointment(appt_id).status == "scheduled"


class TestListing:

    def test_lists_a_patients_appointments(self, empty_db, doctor, patient, appointment):
        assert len(empty_db.get_appointments_by_patient(patient.id)) == 1

    def test_a_patient_with_no_appointments(self, empty_db, patient):
        assert empty_db.get_appointments_by_patient(patient.id) == []

    def test_lists_a_doctors_appointments(self, empty_db, doctor, patient, appointment):
        found = empty_db.get_appointments_by_doctor(doctor.id)
        assert len(found) == 1
        assert found[0].patient_name == "Bob Reed"

    def test_doctor_listing_can_filter_by_status(self, empty_db, doctor, patient):
        book(empty_db, doctor.id, patient.id, time="09:00", status="completed")
        book(empty_db, doctor.id, patient.id, time="11:00", status="scheduled")
        assert len(empty_db.get_appointments_by_doctor(doctor.id, "completed")) == 1
        assert len(empty_db.get_appointments_by_doctor(doctor.id, "scheduled")) == 1

    def test_the_all_filter_means_no_filter(self, empty_db, doctor, patient):
        book(empty_db, doctor.id, patient.id, time="09:00", status="completed")
        book(empty_db, doctor.id, patient.id, time="11:00", status="cancelled")
        assert len(empty_db.get_appointments_by_doctor(doctor.id, "all")) == 2

    def test_lists_every_appointment(self, empty_db, doctor, patient, appointment):
        assert len(empty_db.get_all_appointments()) == 1

    def test_global_listing_can_filter_by_status(self, empty_db, doctor, patient):
        book(empty_db, doctor.id, patient.id, time="09:00", status="completed")
        book(empty_db, doctor.id, patient.id, time="11:00", status="scheduled")
        assert len(empty_db.get_all_appointments("completed")) == 1
        assert len(empty_db.get_all_appointments()) == 2

    def test_listings_drop_appointments_whose_patient_was_deleted(self, empty_db, doctor, patient, appointment):
        # The listings INNER JOIN on patients, so a hard-deleted patient takes
        # their appointment rows out of every view with it
        empty_db.delete_patient(patient.id)
        assert empty_db.get_all_appointments() == []
        assert empty_db.get_appointments_by_doctor(doctor.id) == []


class TestUpdate:

    def test_update_changes_the_stored_row(self, empty_db, appointment):
        appointment.appointment_time = "14:30"
        appointment.notes = "rescheduled"
        assert empty_db.update_appointment(appointment) is True
        loaded = empty_db.get_appointment(appointment.id)
        assert loaded.appointment_time == "14:30"
        assert loaded.notes == "rescheduled"

    def test_updating_a_missing_appointment_returns_false(self, empty_db, appointment):
        appointment.id = 9999
        assert empty_db.update_appointment(appointment) is False

    def test_update_status(self, empty_db, appointment):
        assert empty_db.update_appointment_status(appointment.id, "completed") is True
        assert empty_db.get_appointment(appointment.id).status == "completed"

    def test_updating_the_status_of_a_missing_appointment_returns_false(self, empty_db):
        assert empty_db.update_appointment_status(9999, "completed") is False

    def test_cancel_sets_the_cancelled_status(self, empty_db, appointment):
        assert empty_db.cancel_appointment(appointment.id) is True
        assert empty_db.get_appointment(appointment.id).status == "cancelled"

    def test_cancelling_a_missing_appointment_returns_false(self, empty_db):
        assert empty_db.cancel_appointment(9999) is False


class TestDelete:

    def test_delete_removes_the_row(self, empty_db, appointment):
        assert empty_db.delete_appointment(appointment.id) is True
        assert empty_db.get_appointment(appointment.id) is None

    def test_deleting_a_missing_appointment_returns_false(self, empty_db):
        assert empty_db.delete_appointment(9999) is False


class TestSlotAvailability:

    def test_a_free_slot_is_available(self, empty_db, doctor):
        assert empty_db.is_time_slot_available(doctor.id, datetime.now() + timedelta(days=3), "10:00") is True

    def test_a_booked_slot_is_not_available(self, empty_db, doctor, patient, appointment):
        tomorrow = datetime.now() + timedelta(days=1)
        assert empty_db.is_time_slot_available(doctor.id, tomorrow, "10:00") is False

    def test_a_different_time_the_same_day_is_available(self, empty_db, doctor, patient, appointment):
        tomorrow = datetime.now() + timedelta(days=1)
        assert empty_db.is_time_slot_available(doctor.id, tomorrow, "11:00") is True

    def test_another_doctor_at_the_same_time_is_available(self, empty_db, doctor, patient, appointment):
        from tests.test_database_doctors import make_doctor
        other = make_doctor(empty_db, email="other@hospital.test", doctor_number="DOC200")
        tomorrow = datetime.now() + timedelta(days=1)
        assert empty_db.is_time_slot_available(other.id, tomorrow, "10:00") is True

    def test_cancelling_frees_the_slot(self, empty_db, doctor, patient, appointment):
        empty_db.cancel_appointment(appointment.id)
        tomorrow = datetime.now() + timedelta(days=1)
        assert empty_db.is_time_slot_available(doctor.id, tomorrow, "10:00") is True

    def test_booked_slots_lists_the_taken_times(self, empty_db, doctor, patient, appointment):
        book(empty_db, doctor.id, patient.id, days_ahead=1, time="15:00")
        tomorrow = datetime.now() + timedelta(days=1)
        assert sorted(empty_db.get_booked_slots(doctor.id, tomorrow)) == ["10:00", "15:00"]

    def test_booked_slots_excludes_cancellations(self, empty_db, doctor, patient, appointment):
        empty_db.cancel_appointment(appointment.id)
        tomorrow = datetime.now() + timedelta(days=1)
        assert empty_db.get_booked_slots(doctor.id, tomorrow) == []

    def test_booked_slots_is_empty_on_a_free_day(self, empty_db, doctor):
        assert empty_db.get_booked_slots(doctor.id, datetime.now() + timedelta(days=30)) == []


class TestUpcomingAndPast:

    def test_upcoming_includes_a_future_scheduled_appointment(self, empty_db, doctor, patient, appointment):
        assert len(empty_db.get_upcoming_appointments(patient.id)) == 1

    def test_upcoming_excludes_the_past(self, empty_db, doctor, patient):
        book(empty_db, doctor.id, patient.id, days_ahead=-5)
        assert empty_db.get_upcoming_appointments(patient.id) == []

    def test_upcoming_excludes_cancellations(self, empty_db, doctor, patient, appointment):
        empty_db.cancel_appointment(appointment.id)
        assert empty_db.get_upcoming_appointments(patient.id) == []

    def test_upcoming_is_ordered_soonest_first(self, empty_db, doctor, patient):
        book(empty_db, doctor.id, patient.id, days_ahead=10, time="09:00")
        book(empty_db, doctor.id, patient.id, days_ahead=2, time="09:00")
        upcoming = empty_db.get_upcoming_appointments(patient.id)
        assert upcoming[0].appointment_date < upcoming[1].appointment_date

    def test_upcoming_respects_the_limit(self, empty_db, doctor, patient):
        for day in range(1, 5):
            book(empty_db, doctor.id, patient.id, days_ahead=day)
        assert len(empty_db.get_upcoming_appointments(patient.id, limit=2)) == 2

    def test_past_includes_an_earlier_appointment(self, empty_db, doctor, patient):
        book(empty_db, doctor.id, patient.id, days_ahead=-5)
        assert len(empty_db.get_past_appointments(patient.id)) == 1

    def test_past_includes_completed_and_cancelled_whenever_they_are(self, empty_db, doctor, patient):
        book(empty_db, doctor.id, patient.id, days_ahead=5, status="completed")
        book(empty_db, doctor.id, patient.id, days_ahead=6, status="cancelled")
        assert len(empty_db.get_past_appointments(patient.id)) == 2

    def test_past_excludes_a_future_scheduled_appointment(self, empty_db, doctor, patient, appointment):
        assert empty_db.get_past_appointments(patient.id) == []

    def test_past_respects_the_limit(self, empty_db, doctor, patient):
        for day in range(1, 5):
            book(empty_db, doctor.id, patient.id, days_ahead=-day)
        assert len(empty_db.get_past_appointments(patient.id, limit=3)) == 3
