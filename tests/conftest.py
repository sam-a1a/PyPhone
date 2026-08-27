"""Shared pytest fixtures.

Every test runs against a throwaway SQLite file in a tmp directory, never
against the hospital.db checked into the repo.
"""
import os
import sys

# pygame is imported transitively by the apps package and wants a display.
# Ask SDL for a headless one before anything imports it, so the suite runs
# under CI with no screen attached.
if not os.environ.get("SDL_VIDEODRIVER"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
if not os.environ.get("SDL_AUDIODRIVER"):
    os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta

import pytest

from apps.shared import security
from apps.shared.verification import verification
from apps.shared.database import Database
from apps.shared.models import Admin, Appointment, Doctor, Patient

# bcrypt is slow on purpose, which is the point of it but would add a quarter
# of a second to every fixture. These are genuine bcrypt hashes, just computed
# once per run rather than once per test.
_HASH_CACHE = {}


def cached_hash(password):
    if password not in _HASH_CACHE:
        _HASH_CACHE[password] = security.hash_password(password)
    return _HASH_CACHE[password]


@pytest.fixture
def db(tmp_path):
    """A Database backed by a fresh, empty file.

    There is no demo data: accounts only exist once someone signs up.

    Database is a singleton, so the cached instance is cleared on the way in
    and out; otherwise the first test to build one would pin every later test
    to its database file.
    """
    Database._instance = None
    database = Database(db_path=str(tmp_path / "test_hospital.db"))
    verification.clear_all()
    yield database
    verification.clear_all()
    Database._instance = None


@pytest.fixture
def empty_db(db):
    """Alias for `db`, kept because a new database is already empty."""
    return db


@pytest.fixture
def doctor(empty_db):
    """A saved doctor whose password is "doctorpass"."""
    doc = Doctor(
        name="Dr. Alice Stone", email="alice@hospital.test", phone="+1234567890",
        age=40, doctor_number="DOC100", specialty="Cardiology",
        password_hash=cached_hash("doctorpass"),
        consultation_fee=150.0,
    )
    doc.id = empty_db.add_doctor(doc)
    return doc


@pytest.fixture
def patient(empty_db, doctor):
    """A saved patient assigned to `doctor`."""
    pat = Patient(
        name="Bob Reed", email="bob@patients.test", phone="+1987654321",
        age=52, patient_number="PAT100", disease="Asthma",
        assigned_doctor_id=doctor.id,
    )
    pat.id = empty_db.add_patient(pat)
    return pat


@pytest.fixture
def admin(empty_db):
    """A saved admin whose password is "adminpass"."""
    adm = Admin(
        name="Root Admin", email="root@hospital.test",
        password_hash=cached_hash("adminpass"),
    )
    adm.id = empty_db.add_admin(adm)
    return adm


@pytest.fixture
def appointment(empty_db, doctor, patient):
    """A scheduled appointment for tomorrow at 10:00."""
    appt = Appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        appointment_date=datetime.now() + timedelta(days=1),
        appointment_time="10:00", status="scheduled", notes="Follow-up",
    )
    appt.id = empty_db.add_appointment(appt)
    return appt
