"""Patient CRUD, search and assignment."""
import sqlite3

import pytest

from apps.shared.models import Patient


def make_patient(db, **overrides):
    fields = dict(
        name="Test Patient", email="test@patients.test", phone="+1000000000",
        age=30, patient_number="PAT999", disease="Flu",
    )
    fields.update(overrides)
    pat = Patient(**fields)
    pat.id = db.add_patient(pat)
    return pat


class TestAddAndGet:

    def test_add_returns_a_new_id(self, empty_db):
        assert make_patient(empty_db).id == 1

    def test_get_returns_the_stored_fields(self, empty_db, patient):
        loaded = empty_db.get_patient(patient.id)
        assert loaded.name == "Bob Reed"
        assert loaded.disease == "Asthma"
        assert loaded.patient_number == "PAT100"
        assert loaded.age == 52

    def test_get_unknown_id_returns_none(self, empty_db):
        assert empty_db.get_patient(9999) is None

    def test_get_by_email(self, empty_db, patient):
        assert empty_db.get_patient_by_email("bob@patients.test").id == patient.id

    def test_get_by_unknown_email_returns_none(self, empty_db):
        assert empty_db.get_patient_by_email("nobody@patients.test") is None

    def test_duplicate_email_is_rejected(self, empty_db, patient):
        with pytest.raises(sqlite3.IntegrityError):
            make_patient(empty_db, email="bob@patients.test", patient_number="PAT998")

    def test_duplicate_patient_number_is_rejected(self, empty_db, patient):
        with pytest.raises(sqlite3.IntegrityError):
            make_patient(empty_db, email="other@patients.test", patient_number="PAT100")

    def test_a_patient_added_without_a_password_has_an_empty_hash(self, empty_db, patient):
        # Patients an admin enters have no login until one is set for them;
        # patients who sign up go through register_patient instead
        conn = empty_db.get_connection()
        row = conn.execute("SELECT password_hash FROM patients WHERE id = ?", (patient.id,)).fetchone()
        conn.close()
        assert row["password_hash"] == ""

    def test_a_stored_password_round_trips(self, empty_db):
        pat = Patient(name="With Password", email="wp@patients.test",
                      patient_number="PAT500",
                      password_hash=empty_db.hash_password("mypassword1"))
        pat.id = empty_db.add_patient(pat)
        assert empty_db.get_patient(pat.id).password_hash.startswith("$2b$")

    def test_to_dict_never_leaks_the_password_hash(self, empty_db, patient):
        assert "password_hash" not in empty_db.get_patient(patient.id).to_dict()


class TestListing:

    def test_empty_database_lists_nothing(self, empty_db):
        assert empty_db.get_all_patients() == []

    def test_lists_every_patient(self, empty_db, patient):
        make_patient(empty_db, name="Second", email="s@patients.test", patient_number="PAT2")
        assert len(empty_db.get_all_patients()) == 2

    def test_results_are_ordered_by_name(self, empty_db):
        make_patient(empty_db, name="Zara", email="z@patients.test", patient_number="P1")
        make_patient(empty_db, name="Adam", email="a@patients.test", patient_number="P2")
        assert [p.name for p in empty_db.get_all_patients()] == ["Adam", "Zara"]


class TestFiltering:

    def test_filters_by_disease(self, empty_db, patient):
        make_patient(empty_db, name="Di", email="d@patients.test",
                     patient_number="P5", disease="Diabetes")
        assert [p.name for p in empty_db.get_patients_by_disease("Asthma")] == ["Bob Reed"]

    def test_disease_filter_matches_partially(self, empty_db, patient):
        assert len(empty_db.get_patients_by_disease("sthm")) == 1

    def test_filters_by_assigned_doctor(self, empty_db, doctor, patient):
        make_patient(empty_db, name="Unassigned", email="u@patients.test", patient_number="P6")
        found = empty_db.get_patients_by_doctor(doctor.id)
        assert [p.name for p in found] == ["Bob Reed"]

    def test_unknown_doctor_has_no_patients(self, empty_db, patient):
        assert empty_db.get_patients_by_doctor(9999) == []


class TestSearch:

    def test_finds_by_name(self, empty_db, patient):
        assert len(empty_db.search_patients("Bob")) == 1

    def test_finds_by_email(self, empty_db, patient):
        assert len(empty_db.search_patients("bob@patients")) == 1

    def test_finds_by_disease(self, empty_db, patient):
        assert len(empty_db.search_patients("Asthma")) == 1

    def test_no_match_returns_empty(self, empty_db, patient):
        assert empty_db.search_patients("Nonexistent") == []

    def test_search_within_a_doctors_own_patients(self, empty_db, doctor, patient):
        other = make_patient(empty_db, name="Bobby Other", email="bo@patients.test",
                             patient_number="P7", assigned_doctor_id=None)
        found = empty_db.search_patients_by_doctor(doctor.id, "Bob")
        assert [p.name for p in found] == ["Bob Reed"]
        assert other.name not in [p.name for p in found]

    def test_doctor_scoped_search_with_no_match(self, empty_db, doctor, patient):
        assert empty_db.search_patients_by_doctor(doctor.id, "Nonexistent") == []


class TestUpdate:

    def test_update_changes_the_stored_row(self, empty_db, patient):
        patient.name = "Bob Renamed"
        patient.disease = "Migraine"
        patient.medical_history = "seen in 2024"
        assert empty_db.update_patient(patient) is True
        loaded = empty_db.get_patient(patient.id)
        assert loaded.name == "Bob Renamed"
        assert loaded.disease == "Migraine"
        assert loaded.medical_history == "seen in 2024"

    def test_can_reassign_to_another_doctor(self, empty_db, doctor, patient):
        patient.assigned_doctor_id = None
        empty_db.update_patient(patient)
        assert empty_db.get_patient(patient.id).assigned_doctor_id is None
        assert empty_db.get_doctor_patient_count(doctor.id) == 0

    def test_updating_a_missing_patient_returns_false(self, empty_db, patient):
        patient.id = 9999
        assert empty_db.update_patient(patient) is False


class TestDelete:

    def test_delete_removes_the_row(self, empty_db, patient):
        assert empty_db.delete_patient(patient.id) is True
        assert empty_db.get_patient(patient.id) is None

    def test_deleting_a_missing_patient_returns_false(self, empty_db):
        assert empty_db.delete_patient(9999) is False

    def test_patient_delete_is_permanent_unlike_doctors(self, empty_db, patient):
        empty_db.delete_patient(patient.id)
        assert empty_db.get_all_patients() == []
