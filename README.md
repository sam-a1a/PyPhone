# PyPhone

An iPhone home screen rebuilt in Python and pygame, with two working apps on it:
a **Health** app for patients and a **Health Admin** app for hospital staff, both
backed by SQLite.

[![CI](https://github.com/sam-a1a/PyPhone/actions/workflows/ci.yml/badge.svg)](https://github.com/sam-a1a/PyPhone/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it is

A 420×850 window drawn to look like an iPhone: status bar, Dynamic Island,
app grid, dock, weather widget, page dots and rounded bezel. Tapping an icon
plays a splash animation and opens a full app with its own screen stack,
bottom navigation and persistent login.

| | |
|---|---|
| **Health** | Patient side. Onboarding, sign-up and login (plus mock Apple and Google sign-in sheets), book an appointment with a doctor, appointment history, and a map screen. |
| **Health Admin** | Staff side, with two roles. **Admins** manage doctors, patients and appointments across the hospital and export reports. **Doctors** log in to the same app and see only their own patients and schedule. |

Everything is stored in a local SQLite file (`hospital.db`), created and seeded
the first time you run it.

## Getting started

Requires Python 3.10 or newer.

```bash
git clone https://github.com/sam-a1a/PyPhone.git
cd PyPhone

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

Press `Esc` to quit.

### Demo accounts

The database is seeded on first run:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@admin.com` | `adminadmin` |
| Doctor | `jihan@demo.com` | `jihanjihan` |

These are demo credentials for a local sample database. Change them before
putting this anywhere real.

## Running the tests

```bash
pip install -r requirements.txt
pytest
```

393 tests covering the database layer, password hashing, models, validators
and the drawing helpers. The pygame screens are drawing code and are not unit
tested; the suite imports every one of them so a broken module still fails the
build.

```bash
pytest --cov=apps --cov=config --cov=utils --cov=main --cov-report=term-missing
```

The suite needs no display — `tests/conftest.py` points SDL at its dummy
driver before pygame is imported, which is also how it runs in CI.

Every test runs against a throwaway database in a temp directory, so `pytest`
never touches your `hospital.db`.

## How it is put together

```
main.py                  home screen: app grid, dock, widget, click routing
config.py                screen size, colours, fonts
utils.py                 gradient background, rounded rectangles

components/              home screen pieces: status bar, icons, dock, widgets

apps/
  base_app.py            screen stack, event loop and transitions shared by apps
  app_manager.py         app registry
  splash_screen.py       the zoom-in animation when an icon is tapped

  shared/                the part that is not drawing code
    database.py          SQLite manager: CRUD, queries, statistics, sessions
    models.py            Person, Patient, Doctor, Admin, Appointment
    security.py          password hashing
    validators.py        email, phone, name, age and password rules

  health/                patient app       (screens/ + components/)
  health_admin/          staff app         (screens/ + components/)

tests/                   pytest suite
```

`Database` is a singleton: every screen calls `Database()` and gets the same
instance, sharing one connection path and one login session. Pass
`Database(db_path=...)` or set `PYPHONE_DB_PATH` to point it somewhere else —
which is how the tests keep out of your way.

### Password storage

Passwords are hashed with **bcrypt** (`apps/shared/security.py`), salted per
password and with a work factor of 12.

Earlier versions stored bare SHA-256 digests. Those are unsalted — two accounts
with the same password produced the same digest — and fast enough to brute
force at billions of guesses per second. Any such digest still in the database
is recognised, so nobody is locked out, and it is replaced with a bcrypt hash
the next time that account logs in successfully. No password reset needed.

Two details worth knowing if you touch that file: passwords are folded through
SHA-256 and base64 before bcrypt, because bcrypt ignores everything past 72
bytes and raises on longer input; and legacy digests are compared with
`hmac.compare_digest` rather than `==`.

### Reports

The admin Reports screen exports to PDF (reportlab) and Excel (openpyxl), into
`reports/`.

## Contributing

Pull requests are welcome. Please make sure `pytest` passes, add tests for
anything you change in `apps/shared/`, and match the surrounding style.

## License

[MIT](LICENSE) © Bassam Ghazaleh
