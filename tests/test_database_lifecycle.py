"""Schema creation, demo seeding, statistics and reset."""
import os
from datetime import datetime, timedelta

import pytest

from apps.shared.database import Database
from apps.shared.models import Appointment


def table_names(db):
    conn = db.get_connection()
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    conn.close()
    return {row["name"] for row in rows}


class TestSchema:

    def test_every_table_is_created(self, db):
        assert {"admins", "doctors", "patients", "appointments", "sessions"} <= table_names(db)

    def test_the_database_file_is_created_on_disk(self, db):
        assert os.path.exists(db.db_path)

    def test_creating_tables_twice_is_harmless(self, db):
        db.create_tables()
        assert {"admins", "doctors", "patients"} <= table_names(db)

    def test_rows_come_back_keyed_by_column_name(self, db):
        conn = db.get_connection()
        row = conn.execute("SELECT name FROM admins LIMIT 1").fetchone()
        conn.close()
        assert row["name"]

    def test_an_explicit_path_is_used(self, tmp_path):
        Database._instance = None
        path = str(tmp_path / "custom.db")
        try:
            assert Database(db_path=path).db_path == path
        finally:
            Database._instance = None

    def test_the_path_can_come_from_the_environment(self, tmp_path, monkeypatch):
        Database._instance = None
        path = str(tmp_path / "from_env.db")
        monkeypatch.setenv("PYPHONE_DB_PATH", path)
        try:
            assert Database().db_path == path
        finally:
            Database._instance = None

    def test_it_falls_back_to_hospital_db_in_the_project_root(self, monkeypatch):
        Database._instance = None
        monkeypatch.delenv("PYPHONE_DB_PATH", raising=False)
        monkeypatch.setattr(Database, "create_tables", lambda self: None)
        monkeypatch.setattr(Database, "seed_demo_data", lambda self: None)
        monkeypatch.setattr(Database, "_load_session", lambda self: None)
        try:
            assert Database().db_path.endswith("hospital.db")
        finally:
            Database._instance = None


class TestSeeding:

    def test_a_demo_admin_is_seeded(self, db):
        assert db.get_admin_by_email("admin@admin.com") is not None

    def test_a_demo_doctor_is_seeded(self, db):
        doc = db.get_doctor_by_email("jihan@demo.com")
        assert doc is not None
        assert doc.specialty == "General Practice"

    def test_a_demo_patient_is_seeded(self, db):
        pat = db.get_patient_by_email("ahmad.ali@email.com")
        assert pat is not None
        assert pat.assigned_doctor_id == 1

    def test_no_appointments_are_seeded(self, db):
        assert db.get_all_appointments() == []

    def test_seeding_again_does_not_duplicate_rows(self, db):
        db.seed_demo_data()
        db.seed_demo_data()
        assert len(db.get_all_admins()) == 1
        assert len(db.get_all_doctors()) == 1

    def test_seeding_does_not_run_over_an_existing_database(self, empty_db, admin, doctor):
        # Both tables have rows, so seeding must leave them alone
        empty_db.seed_demo_data()
        assert [a.email for a in empty_db.get_all_admins()] == [admin.email]
        assert [d.email for d in empty_db.get_all_doctors()] == [doctor.email]


class TestAdminCrud:

    def test_get_admin_by_id(self, empty_db, admin):
        assert empty_db.get_admin(admin.id).email == admin.email

    def test_get_unknown_admin_returns_none(self, empty_db):
        assert empty_db.get_admin(9999) is None

    def test_get_unknown_admin_email_returns_none(self, empty_db):
        assert empty_db.get_admin_by_email("nobody@nowhere.test") is None

    def test_listing_shows_only_active_admins(self, empty_db, admin):
        from apps.shared.models import Admin
        empty_db.add_admin(Admin(name="Retired", email="retired@hospital.test",
                                 password_hash="x", is_active=False))
        assert [a.email for a in empty_db.get_all_admins()] == [admin.email]

    def test_admins_are_listed_by_name(self, empty_db):
        from apps.shared.models import Admin
        empty_db.add_admin(Admin(name="Zoe", email="z@hospital.test", password_hash="x"))
        empty_db.add_admin(Admin(name="Abe", email="a@hospital.test", password_hash="x"))
        assert [a.name for a in empty_db.get_all_admins()] == ["Abe", "Zoe"]


class TestStatistics:

    def test_counts_on_an_empty_database(self, empty_db):
        stats = empty_db.get_statistics()
        assert stats["total_doctors"] == 0
        assert stats["total_patients"] == 0
        assert stats["total_appointments"] == 0
        assert stats["total_admins"] == 0

    def test_counts_reflect_the_data(self, empty_db, admin, doctor, patient, appointment):
        stats = empty_db.get_statistics()
        assert stats["total_doctors"] == 1
        assert stats["total_patients"] == 1
        assert stats["total_admins"] == 1
        assert stats["total_appointments"] == 1
        assert stats["pending_appointments"] == 1
        assert stats["completed_appointments"] == 0

    def test_completed_appointments_are_counted_separately(self, empty_db, doctor, patient, appointment):
        empty_db.update_appointment_status(appointment.id, "completed")
        stats = empty_db.get_statistics()
        assert stats["completed_appointments"] == 1
        assert stats["pending_appointments"] == 0

    def test_todays_appointments_are_counted(self, empty_db, doctor, patient):
        appt = Appointment(patient_id=patient.id, doctor_id=doctor.id,
                           appointment_date=datetime.now(), appointment_time="09:00")
        empty_db.add_appointment(appt)
        assert empty_db.get_statistics()["today_appointments"] == 1

    def test_soft_deleted_doctors_are_not_counted(self, empty_db, doctor):
        empty_db.delete_doctor(doctor.id)
        assert empty_db.get_statistics()["total_doctors"] == 0

    def test_patient_statistics(self, empty_db, doctor, patient, appointment):
        stats = empty_db.get_patient_statistics(patient.id)
        assert stats == {"upcoming_appointments": 1, "completed_appointments": 0,
                         "total_appointments": 1}

    def test_patient_statistics_for_someone_with_nothing_booked(self, empty_db, patient):
        stats = empty_db.get_patient_statistics(patient.id)
        assert stats["total_appointments"] == 0

    def test_doctor_statistics(self, empty_db, doctor, patient, appointment):
        stats = empty_db.get_doctor_statistics(doctor.id)
        assert stats["total_patients"] == 1
        assert stats["upcoming_appointments"] == 1
        assert stats["total_appointments"] == 1
        assert stats["completed_appointments"] == 0

    def test_doctor_statistics_count_todays_appointments(self, empty_db, doctor, patient):
        appt = Appointment(patient_id=patient.id, doctor_id=doctor.id,
                           appointment_date=datetime.now(), appointment_time="09:00")
        empty_db.add_appointment(appt)
        assert empty_db.get_doctor_statistics(doctor.id)["today_appointments"] == 1

    def test_doctor_statistics_for_an_unknown_doctor_are_zero(self, empty_db):
        stats = empty_db.get_doctor_statistics(9999)
        assert set(stats.values()) == {0}


class TestReset:

    def test_reset_clears_the_data_and_reseeds(self, empty_db, admin, doctor, patient, appointment):
        empty_db.reset_database()
        assert empty_db.get_all_appointments() == []
        assert [a.email for a in empty_db.get_all_admins()] == ["admin@admin.com"]
        assert [d.email for d in empty_db.get_all_doctors()] == ["jihan@demo.com"]

    def test_reset_logs_the_current_user_out(self, empty_db, admin):
        empty_db.save_session("admin", admin.id, admin.email)
        empty_db.reset_database()
        assert empty_db.is_logged_in() is False

    def test_the_reseeded_admin_can_log_in(self, empty_db):
        empty_db.reset_database()
        assert empty_db.authenticate_admin("admin@admin.com", "adminadmin") is not None
