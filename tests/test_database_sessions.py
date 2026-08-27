"""Session persistence: who is logged in, and surviving a restart."""
from apps.shared.database import Database


class TestFreshSession:

    def test_nobody_is_logged_in_initially(self, empty_db):
        assert empty_db.is_logged_in() is False
        assert empty_db.get_current_user_id() is None
        assert empty_db.get_current_user_type() is None

    def test_role_checks_are_false_when_logged_out(self, empty_db):
        assert empty_db.is_admin() is False
        assert empty_db.is_doctor() is False

    def test_current_user_objects_are_none_when_logged_out(self, empty_db):
        assert empty_db.get_current_admin() is None
        assert empty_db.get_current_doctor() is None
        assert empty_db.get_current_patient() is None


class TestSaveAndClear:

    def test_saving_a_session_logs_the_user_in(self, empty_db, admin):
        empty_db.save_session("admin", admin.id, admin.email)
        assert empty_db.is_logged_in() is True
        assert empty_db.get_current_user_id() == admin.id
        assert empty_db.get_current_user_type() == "admin"

    def test_get_current_user_returns_the_details(self, empty_db, admin):
        empty_db.save_session("admin", admin.id, admin.email)
        assert empty_db.get_current_user() == {
            "logged_in": True, "user_type": "admin",
            "user_id": admin.id, "email": admin.email,
        }

    def test_get_current_user_returns_a_copy(self, empty_db, admin):
        # Callers must not be able to mutate the session by accident
        empty_db.save_session("admin", admin.id, admin.email)
        empty_db.get_current_user()["user_id"] = 999
        assert empty_db.get_current_user_id() == admin.id

    def test_clearing_logs_the_user_out(self, empty_db, admin):
        empty_db.save_session("admin", admin.id, admin.email)
        empty_db.clear_session()
        assert empty_db.is_logged_in() is False
        assert empty_db.get_current_user_id() is None

    def test_only_one_session_is_kept(self, empty_db, admin, doctor):
        empty_db.save_session("admin", admin.id, admin.email)
        empty_db.save_session("doctor", doctor.id, doctor.email)
        conn = empty_db.get_connection()
        count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        conn.close()
        assert count == 1
        assert empty_db.get_current_user_type() == "doctor"


class TestRoles:

    def test_admin_role(self, empty_db, admin):
        empty_db.save_session("admin", admin.id, admin.email)
        assert empty_db.is_admin() is True
        assert empty_db.is_doctor() is False
        assert empty_db.get_current_admin().email == admin.email
        assert empty_db.get_current_doctor() is None

    def test_doctor_role(self, empty_db, doctor):
        empty_db.save_session("doctor", doctor.id, doctor.email)
        assert empty_db.is_doctor() is True
        assert empty_db.is_admin() is False
        assert empty_db.get_current_doctor().email == doctor.email
        assert empty_db.get_current_admin() is None

    def test_patient_role(self, empty_db, patient):
        empty_db.save_session("patient", patient.id, patient.email)
        assert empty_db.is_admin() is False
        assert empty_db.is_doctor() is False
        assert empty_db.get_current_patient().email == patient.email


class TestSessionSurvivesRestart:

    @staticmethod
    def reopen(db):
        """Drop the singleton and build a new Database over the same file."""
        path = db.db_path
        Database._instance = None
        return Database(db_path=path)

    def test_a_saved_session_is_restored(self, empty_db, admin):
        empty_db.save_session("admin", admin.id, admin.email)
        reopened = self.reopen(empty_db)
        assert reopened.is_logged_in() is True
        assert reopened.get_current_user_type() == "admin"
        assert reopened.get_current_user_id() == admin.id

    def test_a_cleared_session_stays_cleared(self, empty_db, admin):
        empty_db.save_session("admin", admin.id, admin.email)
        empty_db.clear_session()
        assert self.reopen(empty_db).is_logged_in() is False

    def test_a_session_for_a_deleted_user_is_discarded(self, empty_db, patient):
        empty_db.save_session("patient", patient.id, patient.email)
        empty_db.delete_patient(patient.id)
        reopened = self.reopen(empty_db)
        assert reopened.is_logged_in() is False

    def test_a_stale_session_is_wiped_from_the_database_too(self, empty_db, patient):
        empty_db.save_session("patient", patient.id, patient.email)
        empty_db.delete_patient(patient.id)
        reopened = self.reopen(empty_db)
        conn = reopened.get_connection()
        count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        conn.close()
        assert count == 0

    def test_a_soft_deleted_doctors_session_survives(self, empty_db, doctor):
        # get_doctor ignores is_active, so deactivation does not end a session
        # already in progress; the next login attempt is what blocks them
        empty_db.save_session("doctor", doctor.id, doctor.email)
        empty_db.delete_doctor(doctor.id)
        assert self.reopen(empty_db).is_logged_in() is True


class TestSingleton:

    def test_repeated_construction_returns_the_same_object(self, db):
        assert Database() is db

    def test_the_second_construction_does_not_change_the_path(self, db):
        assert Database(db_path="/somewhere/else.db").db_path == db.db_path
