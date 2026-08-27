<div align="center">

# PyPhone

**An iPhone, rebuilt in Python.**

A pixel-drawn iOS home screen running on pygame — Dynamic Island, app grid,
dock, widgets and all — with two complete, database-backed applications
installed on it.

[![CI](https://github.com/sam-a1a/PyPhone/actions/workflows/ci.yml/badge.svg)](https://github.com/sam-a1a/PyPhone/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-393%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen.svg)](#running-the-tests)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**~12,400 lines · 24 screens · 2 apps · 5 SQLite tables · 0 UI frameworks**

</div>

---

## What this is

There is no GUI toolkit here. No Tkinter, no Qt, no Kivy, no web view. Every
button, input field, dropdown, table, card, ring and animation is drawn from
pygame primitives, one shape at a time — and then wired into two applications
with real logins, real persistence and real business logic.

**The phone.** A 420×850 window styled as an iPhone: a status bar with a
pill-shaped Dynamic Island, live clock, battery and signal glyphs; a four-across app
grid over a three-stop sunset gradient computed per scanline; a translucent
dock with a notification badge; a full-width weather widget; page dots; and a
rounded black bezel composited over the top. Tapping an icon plays a splash
animation — the icon holds, then zooms as the app takes over the screen.

**Two apps that actually work.** Not mockups. They log you in, remember you
after you quit, read and write a SQLite database, and enforce who is allowed
to see what.

## The apps

### Health — the patient side

<table>
<tr><td width="50%">

**Getting in**
- Onboarding carousel
- Sign-up with live inline validation — errors expand and collapse with an
  animated height transition as you type
- Login, forgot-password flow, terms screen
- Apple and Google sign-in modal sheets, drawn to match the real system
  consent sheets

</td><td width="50%">

**Once you are in**
- Dashboard with health stat cards for heart rate, calories and sleep
- A segmented activity ring tracking steps against a daily goal
- Upcoming appointments, pulled live from the database
- Appointment history
- A map screen with location pins

</td></tr>
</table>

**Booking an appointment** is a four-stage flow: browse doctors → doctor
detail with specialty and consultation fee → pick from eight time slots for a
chosen day → confirm. Slots already taken are queried from the database and
shown as unavailable, and availability is re-checked at the moment of booking,
so two patients cannot take the same slot.

### Health Admin — the staff side

The same app serves two roles, and knows the difference.

| | **Administrator** | **Doctor** |
|---|---|---|
| Dashboard | Hospital-wide statistics, doctor overview | Own patients, own schedule, today's list |
| Doctors | Full CRUD | — |
| Patients | Every patient | Only their assigned patients |
| Appointments | All, filterable by status | Only their own |
| Reports | Export | — |

- **Doctors and patients** get full list → view → add → edit flows with
  per-field validation and dropdowns for specialty and disease. Doctors are
  soft-deleted, so their appointment history survives.
- **Appointments** can be marked complete or cancelled, and filtered by status.
- **Scoping is enforced in the queries, not the UI.** When a doctor is logged
  in, the patients screen searches only their assigned patients and the
  appointments screen loads only their own — different SQL, not a hidden
  button.
- **Reports** export doctors, patients, appointments or hospital statistics to
  **PDF** (reportlab) or **Excel** (openpyxl), written to `reports/`.

## Under the hood

**122 drawing routines** build the interface. Rounded rectangles are
composited through a per-pixel alpha mask rather than pygame's built-in
`border_radius`, so corners stay smooth at any radius; circles go through
`pygame.gfxdraw` for anti-aliasing. Icons are loaded from 33 icon assets,
scaled with `smoothscale`, cached after first use, and fall back to a
generated rounded-square if a file is missing.

**A 59-method SQLite layer** (`apps/shared/database.py`) covers five tables —
admins, doctors, patients, appointments, sessions — with foreign keys,
soft deletes, joined queries for appointment listings, availability checks,
and statistics rollups for each of the three dashboards.

**Sessions persist to disk.** Close the window mid-session and reopen it: the
app checks the session table, confirms the user still exists, and drops you
back where you were. Delete that user and the stale session is cleaned up
instead.

**Passwords are hashed with bcrypt** — see [Password storage](#password-storage).

**393 tests** and a CI matrix across Python 3.10–3.13.

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

Tap **Health** (row 1) or **Admin** (row 4). Press `Esc` to go back, and again
to quit.

### Demo accounts

The database is created and seeded on first run.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@admin.com` | `adminadmin` |
| Doctor | `jihan@demo.com` | `jihanjihan` |

Demo credentials for a local sample database. Change them before putting this
anywhere real.

## Running the tests

```bash
pip install -r requirements.txt
pytest
```

```
393 passed

Name                        Stmts   Miss  Cover
------------------------------------------------
apps/shared/database.py       529      0   100%
apps/shared/models.py          78      0   100%
apps/shared/security.py        39      0   100%
apps/shared/validators.py      51      0   100%
config.py                      37      7    81%
utils.py                       40      0   100%
------------------------------------------------
TOTAL                         778      7    99%
```

CI fails the build if that total drops below 95%.

The suite covers password hashing, the whole SQLite layer, the models, the
validators, and the drawing helpers that can render to an off-screen surface.
The pygame screens are drawing code and are not unit tested — but every one of
them is imported by `tests/test_imports.py`, so a module that no longer even
loads fails the build.

It needs no display: `tests/conftest.py` points SDL at its dummy driver before
pygame is imported, which is also how it runs in CI. Every test gets a
throwaway database in a temp directory, so `pytest` never touches your
`hospital.db`.

```bash
pytest --cov=apps.shared --cov=config --cov=utils --cov-report=term-missing
```

## Project layout

```
main.py                  home screen: app grid, dock, widget, click routing
config.py                screen size, colour palette, fonts
utils.py                 sunset gradient, alpha-masked rounded rectangles

components/              status bar + Dynamic Island, icons, dock, widgets

apps/
  base_app.py            screen stack, event loop, header and bezel
  app_manager.py         app registry
  splash_screen.py       the zoom-in animation when an icon is tapped

  shared/                everything that is not drawing code
    database.py          59 methods: CRUD, queries, statistics, sessions
    models.py            Person → Patient / Doctor, plus Admin, Appointment
    security.py          bcrypt hashing and legacy migration
    validators.py        email, phone, name, age, password rules

  health/                patient app        11 screens + 4 component modules
  health_admin/          staff app          13 screens + 6 component modules

tests/                   393 tests across 11 files
.github/workflows/       CI on Python 3.10, 3.11, 3.12, 3.13
```

### Design notes

`Person` is subclassed by `Patient` and `Doctor`, each extending `to_dict()` —
the models are dataclasses, so equality and `from_dict()` round-trips come for
free.

`Database` is a singleton: every screen calls `Database()` and gets the same
instance, sharing one connection path and one login session. Pass
`Database(db_path=...)` or set `PYPHONE_DB_PATH` to point it elsewhere — which
is how the tests keep out of your way.

Screens are self-contained objects with `draw()`, `handle_event()` and
`update()`, held in a dictionary by the app that owns them and swapped by name,
so adding a screen means adding one file and one dictionary entry.

### Password storage

Passwords are hashed with **bcrypt**, salted per password, work factor 12
(`apps/shared/security.py`).

Earlier versions stored bare SHA-256 digests. Those are unsalted — two accounts
with the same password produced the same digest — and fast enough to brute
force at billions of guesses per second. Any such digest still in a database is
recognised, so nobody is locked out, and is replaced with a bcrypt hash the
next time that account logs in successfully. No password reset needed.

Two details worth knowing if you touch that file: passwords are folded through
SHA-256 and base64 before bcrypt, because bcrypt ignores everything past 72
bytes and raises on longer input; and legacy digests are compared with
`hmac.compare_digest` rather than `==`.

## Contributing

Pull requests are welcome. Please keep `pytest` green, add tests for anything
you change under `apps/shared/`, and match the surrounding style.

## License

[MIT](LICENSE) © Bassam Ghazaleh
