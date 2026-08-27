"""Doctor CRUD, search and filtering."""
import sqlite3

import pytest

from apps.shared.models import Doctor
from tests.conftest import cached_hash


def make_doctor(db, **overrides):
    fields = dict(
        name="Dr. Test", email="test@hospital.test", phone="+1000000000",
        age=45, doctor_number="DOC999", specialty="Pediatrics",
        password_hash=cached_hash("doctorpass"),
    )
    fields.update(overrides)
    doc = Doctor(**fields)
    doc.id = db.add_doctor(doc)
    return doc


class TestAddAndGet:

    def test_add_returns_a_new_id(self, empty_db):
        assert make_doctor(empty_db).id == 1

    def test_ids_increment(self, empty_db):
        first = make_doctor(empty_db)
        second = make_doctor(empty_db, email="two@hospital.test", doctor_number="DOC998")
        assert second.id == first.id + 1

    def test_get_returns_the_stored_fields(self, empty_db, doctor):
        loaded = empty_db.get_doctor(doctor.id)
        assert loaded.name == "Dr. Alice Stone"
        assert loaded.email == "alice@hospital.test"
        assert loaded.specialty == "Cardiology"
        assert loaded.consultation_fee == 150.0

    def test_get_unknown_id_returns_none(self, empty_db):
        assert empty_db.get_doctor(9999) is None

    def test_get_by_email(self, empty_db, doctor):
        assert empty_db.get_doctor_by_email("alice@hospital.test").id == doctor.id

    def test_get_by_unknown_email_returns_none(self, empty_db, doctor):
        assert empty_db.get_doctor_by_email("nobody@hospital.test") is None

    def test_created_at_is_recorded(self, empty_db, doctor):
        assert empty_db.get_doctor(doctor.id).created_at is not None

    def test_defaults_are_applied(self, empty_db):
        doc = make_doctor(empty_db)
        loaded = empty_db.get_doctor(doc.id)
        assert loaded.max_patients == 20
        assert loaded.available_days == "Mon,Tue,Wed,Thu,Fri"
        assert loaded.available_hours == "09:00-17:00"
        assert loaded.is_active is True

    def test_duplicate_email_is_rejected(self, empty_db, doctor):
        with pytest.raises(sqlite3.IntegrityError):
            make_doctor(empty_db, email="alice@hospital.test", doctor_number="DOC998")

    def test_duplicate_doctor_number_is_rejected(self, empty_db, doctor):
        with pytest.raises(sqlite3.IntegrityError):
            make_doctor(empty_db, email="other@hospital.test", doctor_number="DOC100")


class TestListing:

    def test_empty_database_lists_nothing(self, empty_db):
        assert empty_db.get_all_doctors() == []

    def test_lists_active_doctors_by_default(self, empty_db, doctor):
        make_doctor(empty_db, name="Dr. Zed", email="zed@hospital.test",
                    doctor_number="DOC101", is_active=False)
        listed = empty_db.get_all_doctors()
        assert [d.name for d in listed] == ["Dr. Alice Stone"]

    def test_can_include_inactive_doctors(self, empty_db, doctor):
        make_doctor(empty_db, name="Dr. Zed", email="zed@hospital.test",
                    doctor_number="DOC101", is_active=False)
        assert len(empty_db.get_all_doctors(active_only=False)) == 2

    def test_results_are_ordered_by_name(self, empty_db):
        make_doctor(empty_db, name="Dr. Zoe", email="z@hospital.test", doctor_number="D1")
        make_doctor(empty_db, name="Dr. Adam", email="a@hospital.test", doctor_number="D2")
        assert [d.name for d in empty_db.get_all_doctors()] == ["Dr. Adam", "Dr. Zoe"]


class TestSpecialty:

    def test_filters_by_specialty(self, empty_db, doctor):
        make_doctor(empty_db, name="Dr. Skin", email="skin@hospital.test",
                    doctor_number="D3", specialty="Dermatology")
        found = empty_db.get_doctors_by_specialty("Cardiology")
        assert [d.name for d in found] == ["Dr. Alice Stone"]

    def test_specialty_match_is_exact(self, empty_db, doctor):
        assert empty_db.get_doctors_by_specialty("Cardio") == []

    def test_inactive_doctors_are_excluded(self, empty_db, doctor):
        empty_db.delete_doctor(doctor.id)
        assert empty_db.get_doctors_by_specialty("Cardiology") == []


class TestSearch:

    def test_finds_by_partial_name(self, empty_db, doctor):
        assert len(empty_db.search_doctors("Alice")) == 1

    def test_finds_by_partial_specialty(self, empty_db, doctor):
        assert len(empty_db.search_doctors("Cardio")) == 1

    def test_search_is_case_insensitive(self, empty_db, doctor):
        # SQLite LIKE is case-insensitive for ASCII
        assert len(empty_db.search_doctors("alice")) == 1

    def test_no_match_returns_empty(self, empty_db, doctor):
        assert empty_db.search_doctors("Nonexistent") == []

    def test_empty_query_matches_everything(self, empty_db, doctor):
        assert len(empty_db.search_doctors("")) == 1

    def test_inactive_doctors_are_not_searchable(self, empty_db, doctor):
        empty_db.delete_doctor(doctor.id)
        assert empty_db.search_doctors("Alice") == []

    def test_a_wildcard_in_the_query_is_treated_as_a_literal(self, empty_db, doctor):
        # "%" is escaped by parameter binding, not by the LIKE grammar, so this
        # documents that a bare "%" still matches everything
        assert len(empty_db.search_doctors("%")) == 1


class TestUpdate:

    def test_update_changes_the_stored_row(self, empty_db, doctor):
        doctor.name = "Dr. Alice Renamed"
        doctor.specialty = "Neurology"
        doctor.consultation_fee = 200.0
        assert empty_db.update_doctor(doctor) is True
        loaded = empty_db.get_doctor(doctor.id)
        assert loaded.name == "Dr. Alice Renamed"
        assert loaded.specialty == "Neurology"
        assert loaded.consultation_fee == 200.0

    def test_update_does_not_touch_the_password(self, empty_db, doctor):
        before = empty_db.get_doctor(doctor.id).password_hash
        doctor.name = "Dr. Renamed"
        empty_db.update_doctor(doctor)
        assert empty_db.get_doctor(doctor.id).password_hash == before

    def test_updating_a_missing_doctor_returns_false(self, empty_db, doctor):
        doctor.id = 9999
        assert empty_db.update_doctor(doctor) is False

    def test_can_reactivate_via_update(self, empty_db, doctor):
        empty_db.delete_doctor(doctor.id)
        doctor.is_active = True
        empty_db.update_doctor(doctor)
        assert empty_db.get_doctor(doctor.id).is_active is True


class TestDelete:

    def test_delete_is_a_soft_delete(self, empty_db, doctor):
        assert empty_db.delete_doctor(doctor.id) is True
        assert empty_db.get_doctor(doctor.id) is not None
        assert empty_db.get_doctor(doctor.id).is_active is False

    def test_deleted_doctor_is_hidden_from_listings(self, empty_db, doctor):
        empty_db.delete_doctor(doctor.id)
        assert empty_db.get_all_doctors() == []

    def test_deleting_a_missing_doctor_returns_false(self, empty_db):
        assert empty_db.delete_doctor(9999) is False


class TestPatientCount:

    def test_counts_assigned_patients(self, empty_db, doctor, patient):
        assert empty_db.get_doctor_patient_count(doctor.id) == 1

    def test_zero_when_nobody_is_assigned(self, empty_db, doctor):
        assert empty_db.get_doctor_patient_count(doctor.id) == 0

    def test_unknown_doctor_counts_zero(self, empty_db):
        assert empty_db.get_doctor_patient_count(9999) == 0
