"""Login paths, and the migration of old SHA-256 rows to bcrypt."""
import hashlib

import pytest

from apps.shared import security
from apps.shared.database import Database
from apps.shared.models import Admin, Doctor, Patient
from tests.conftest import cached_hash


def stored_hash(db, table, user_id):
    conn = db.get_connection()
    row = conn.execute(f"SELECT password_hash FROM {table} WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row["password_hash"]


class TestAdminLogin:

    def test_correct_credentials_return_the_admin(self, empty_db, admin):
        result = empty_db.authenticate_admin("root@hospital.test", "adminpass")
        assert result is not None
        assert result.email == "root@hospital.test"

    def test_wrong_password_returns_none(self, empty_db, admin):
        assert empty_db.authenticate_admin("root@hospital.test", "wrongpass") is None

    def test_unknown_email_returns_none(self, empty_db, admin):
        assert empty_db.authenticate_admin("nobody@hospital.test", "adminpass") is None

    def test_inactive_admin_cannot_log_in(self, empty_db):
        inactive = Admin(name="Old Admin", email="old@hospital.test",
                         password_hash=cached_hash("adminpass"), is_active=False)
        empty_db.add_admin(inactive)
        assert empty_db.authenticate_admin("old@hospital.test", "adminpass") is None

    def test_empty_password_does_not_log_in(self, empty_db, admin):
        assert empty_db.authenticate_admin("root@hospital.test", "") is None


class TestDoctorLogin:

    def test_correct_credentials_return_the_doctor(self, empty_db, doctor):
        result = empty_db.authenticate_doctor("alice@hospital.test", "doctorpass")
        assert result is not None
        assert result.specialty == "Cardiology"

    def test_wrong_password_returns_none(self, empty_db, doctor):
        assert empty_db.authenticate_doctor("alice@hospital.test", "nope") is None

    def test_deactivated_doctor_cannot_log_in(self, empty_db, doctor):
        empty_db.delete_doctor(doctor.id)  # soft delete
        assert empty_db.authenticate_doctor("alice@hospital.test", "doctorpass") is None


class TestPatientLogin:

    def test_patient_with_a_password_can_log_in(self, empty_db, patient):
        conn = empty_db.get_connection()
        conn.execute("UPDATE patients SET password_hash = ? WHERE id = ?",
                     (cached_hash("patientpass"), patient.id))
        conn.commit()
        conn.close()
        result = empty_db.authenticate_patient("bob@patients.test", "patientpass")
        assert result is not None
        assert result.id == patient.id

    def test_patient_without_a_password_cannot_log_in(self, empty_db, patient):
        # add_patient stores an empty hash; an empty stored hash must never
        # authenticate, whatever is typed in
        assert stored_hash(empty_db, "patients", patient.id) == ""
        assert empty_db.authenticate_patient("bob@patients.test", "") is None
        assert empty_db.authenticate_patient("bob@patients.test", "anything") is None

    def test_wrong_password_returns_none(self, empty_db, patient):
        conn = empty_db.get_connection()
        conn.execute("UPDATE patients SET password_hash = ? WHERE id = ?",
                     (cached_hash("patientpass"), patient.id))
        conn.commit()
        conn.close()
        assert empty_db.authenticate_patient("bob@patients.test", "guess") is None


class TestPasswordsAreNotStoredInTheClear:

    def test_admin_password_is_not_recoverable_from_the_row(self, empty_db, admin):
        assert "adminpass" not in stored_hash(empty_db, "admins", admin.id)

    def test_two_users_with_the_same_password_get_different_hashes(self, empty_db):
        first = Admin(name="A", email="a@hospital.test",
                      password_hash=empty_db.hash_password("identical"))
        second = Admin(name="B", email="b@hospital.test",
                       password_hash=empty_db.hash_password("identical"))
        first_id = empty_db.add_admin(first)
        second_id = empty_db.add_admin(second)
        assert stored_hash(empty_db, "admins", first_id) != stored_hash(empty_db, "admins", second_id)

    def test_seeded_demo_accounts_are_hashed_with_bcrypt(self, db):
        # The seeding path must not reintroduce the old scheme
        assert stored_hash(db, "admins", 1).startswith("$2b$")
        assert stored_hash(db, "doctors", 1).startswith("$2b$")

    def test_seeded_demo_admin_can_log_in(self, db):
        assert db.authenticate_admin("admin@admin.com", "adminadmin") is not None

    def test_seeded_demo_doctor_can_log_in(self, db):
        assert db.authenticate_doctor("jihan@demo.com", "jihanjihan") is not None


class TestLegacyHashMigration:
    """Rows written by the old SHA-256 code, still in existing hospital.db files."""

    @staticmethod
    def make_legacy(db, table, user_id, password):
        legacy = hashlib.sha256(password.encode()).hexdigest()
        conn = db.get_connection()
        conn.execute(f"UPDATE {table} SET password_hash = ? WHERE id = ?", (legacy, user_id))
        conn.commit()
        conn.close()
        return legacy

    def test_admin_with_a_legacy_hash_can_still_log_in(self, empty_db, admin):
        self.make_legacy(empty_db, "admins", admin.id, "adminpass")
        assert empty_db.authenticate_admin("root@hospital.test", "adminpass") is not None

    def test_successful_login_replaces_the_legacy_hash(self, empty_db, admin):
        legacy = self.make_legacy(empty_db, "admins", admin.id, "adminpass")
        empty_db.authenticate_admin("root@hospital.test", "adminpass")
        upgraded = stored_hash(empty_db, "admins", admin.id)
        assert upgraded != legacy
        assert upgraded.startswith("$2b$")

    def test_the_password_still_works_after_the_upgrade(self, empty_db, admin):
        self.make_legacy(empty_db, "admins", admin.id, "adminpass")
        empty_db.authenticate_admin("root@hospital.test", "adminpass")
        assert empty_db.authenticate_admin("root@hospital.test", "adminpass") is not None
        assert empty_db.authenticate_admin("root@hospital.test", "adminpass2") is None

    def test_a_failed_login_does_not_touch_the_hash(self, empty_db, admin):
        legacy = self.make_legacy(empty_db, "admins", admin.id, "adminpass")
        empty_db.authenticate_admin("root@hospital.test", "wrong")
        assert stored_hash(empty_db, "admins", admin.id) == legacy

    def test_doctor_legacy_hash_is_upgraded(self, empty_db, doctor):
        self.make_legacy(empty_db, "doctors", doctor.id, "doctorpass")
        assert empty_db.authenticate_doctor("alice@hospital.test", "doctorpass") is not None
        assert stored_hash(empty_db, "doctors", doctor.id).startswith("$2b$")

    def test_patient_legacy_hash_is_upgraded(self, empty_db, patient):
        self.make_legacy(empty_db, "patients", patient.id, "patientpass")
        assert empty_db.authenticate_patient("bob@patients.test", "patientpass") is not None
        assert stored_hash(empty_db, "patients", patient.id).startswith("$2b$")

    def test_an_already_current_hash_is_left_alone(self, empty_db, admin):
        before = stored_hash(empty_db, "admins", admin.id)
        empty_db.authenticate_admin("root@hospital.test", "adminpass")
        assert stored_hash(empty_db, "admins", admin.id) == before


class TestUpgradeHelper:

    def test_rejects_an_unknown_table(self, empty_db, admin):
        # The table name is interpolated into SQL, so it must be an allowlist
        with pytest.raises(ValueError):
            empty_db._upgrade_password_hash("admins; DROP TABLE admins", admin.id, "x")

    @pytest.mark.parametrize("table", ["admins", "doctors", "patients"])
    def test_every_table_with_a_password_column_is_allowlisted(self, table):
        assert table in Database._PASSWORD_TABLES

    def test_upgrades_the_hash_it_is_given(self, empty_db, admin):
        before = stored_hash(empty_db, "admins", admin.id)
        empty_db._upgrade_password_hash("admins", admin.id, "brand-new-password")
        after = stored_hash(empty_db, "admins", admin.id)
        assert after != before
        assert security.verify_password("brand-new-password", after)


class TestDatabaseDelegatesToSecurity:

    def test_hash_password_matches_the_security_module(self, db):
        digest = db.hash_password("delegation")
        assert security.verify_password("delegation", digest)

    def test_verify_password_matches_the_security_module(self, db):
        digest = security.hash_password("delegation")
        assert db.verify_password("delegation", digest) is True
        assert db.verify_password("nope", digest) is False
