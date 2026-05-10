#SQLite Database manager
import hashlib
import os
import sqlite3
from datetime import datetime
from typing import List, Optional

from apps.shared.models import Patient, Doctor, Appointment, Admin

class Database:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(project_root, "hospital.db")
        self._initialized = True

        self._session = {
            "logged_in": False,
            "user_type": None,  # "admin", "doctor", "patient"
            "user_id": None,
            "email": None
        }

        self.create_tables()
        self.seed_demo_data()

        # Try to restore previous session from disk
        self._load_session()

    def get_connection(self):
        #Get database connection
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        ''')

        # Doctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                age INTEGER,
                doctor_number TEXT UNIQUE,
                specialty TEXT,
                password_hash TEXT,
                is_active INTEGER DEFAULT 1,
                max_patients INTEGER DEFAULT 20,
                consultation_fee REAL DEFAULT 0,
                available_days TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
                available_hours TEXT DEFAULT '09:00-17:00',
                created_at TEXT
            )
        ''')

        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                age INTEGER,
                patient_number TEXT UNIQUE,
                disease TEXT,
                assigned_doctor_id INTEGER,
                medical_history TEXT,
                password_hash TEXT,
                created_at TEXT,
                FOREIGN KEY (assigned_doctor_id) REFERENCES doctors(id)
            )
        ''')

        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_date TEXT,
                appointment_time TEXT,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        ''')

        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                email TEXT,
                login_time TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password, password_hash):
        return self.hash_password(password) == password_hash

    # Session Management
    def _load_session(self):
        # Load active session from database if it exists
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()

        if row:
            # Check if user still exists (basic validity check)
            exists = False
            if row['user_type'] == 'admin':
                exists = self.get_admin(row['user_id']) is not None
            elif row['user_type'] == 'doctor':
                exists = self.get_doctor(row['user_id']) is not None
            elif row['user_type'] == 'patient':
                exists = self.get_patient(row['user_id']) is not None

            if exists:
                self._session = {
                    "logged_in": True,
                    "user_type": row['user_type'],
                    "user_id": row['user_id'],
                    "email": row['email']
                }
            else:
                # Invalid session, clear it
                self.clear_session()

    def is_logged_in(self) -> bool:
        return self._session.get("logged_in", False)

    def save_session(self, user_type: str, user_id: int, email: str):
        #Save session to memory and database
        # 1. Update Memory
        self._session = {
            "logged_in": True,
            "user_type": user_type,
            "user_id": user_id,
            "email": email
        }

        # 2. Update Database
        conn = self.get_connection()
        cursor = conn.cursor()

        # Clear any old sessions
        cursor.execute('DELETE FROM sessions')

        # Insert new session
        cursor.execute('''
            INSERT INTO sessions (user_type, user_id, email, login_time)
            VALUES (?, ?, ?, ?)
        ''', (user_type, user_id, email, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def clear_session(self):
        #Clear session from memory and database
        # 1. Clear Memory
        self._session = {
            "logged_in": False,
            "user_type": None,
            "user_id": None,
            "email": None
        }

        # 2. Clear Database
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions')
        conn.commit()
        conn.close()

    def get_current_user(self) -> dict:
        return self._session.copy()

    def get_current_user_id(self) -> Optional[int]:
        if self._session.get("logged_in"):
            return self._session.get("user_id")
        return None

    def get_current_user_type(self) -> Optional[str]:
        #Returns 'admin', 'doctor', or 'patient'
        if self._session.get("logged_in"):
            return self._session.get("user_type")
        return None

    def is_admin(self) -> bool:
        #Check if current user is an admin
        return self._session.get("user_type") == "admin"

    def is_doctor(self) -> bool:
        #Check if current user is a doctor
        return self._session.get("user_type") == "doctor"

    def get_current_patient(self) -> Optional[Patient]:
        if self._session.get("logged_in") and self._session.get("user_type") == "patient":
            return self.get_patient(self._session.get("user_id"))
        return None

    def get_current_doctor(self) -> Optional[Doctor]:
        if self._session.get("logged_in") and self._session.get("user_type") == "doctor":
            return self.get_doctor(self._session.get("user_id"))
        return None

    def get_current_admin(self) -> Optional[Admin]:
        if self._session.get("logged_in") and self._session.get("user_type") == "admin":
            return self.get_admin(self._session.get("user_id"))
        return None

    #Admin Methods
    def add_admin(self, admin: Admin) -> int:
        #Add a new admin
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO admins (name, email, password_hash, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            admin.name, admin.email, admin.password_hash,
            1 if admin.is_active else 0,
            datetime.now().isoformat()
        ))

        admin_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return admin_id

    def get_admin(self, admin_id: int) -> Optional[Admin]:
        #Get admin by ID
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE id = ?', (admin_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_admin(row)
        return None

    def get_admin_by_email(self, email: str) -> Optional[Admin]:
        #Get admin by email
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_admin(row)
        return None

    def authenticate_admin(self, email: str, password: str) -> Optional[Admin]:
        #Authenticate an admin. Returns Admin if successful, None otherwise
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE email = ? AND is_active = 1', (email,))
        row = cursor.fetchone()
        conn.close()
        if row and self.verify_password(password, row['password_hash']):
            return self._row_to_admin(row)
        return None

    def get_all_admins(self) -> List[Admin]:
        #Get all admins
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE is_active = 1 ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_admin(row) for row in rows]

    # Doc methods
    def add_doctor(self, doctor: Doctor) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO doctors (name, email, phone, age, doctor_number, specialty,
                               password_hash, is_active, max_patients, consultation_fee,
                               available_days, available_hours, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doctor.name, doctor.email, doctor.phone, doctor.age,
            doctor.doctor_number, doctor.specialty, doctor.password_hash,
            1 if doctor.is_active else 0, doctor.max_patients, doctor.consultation_fee,
            doctor.available_days, doctor.available_hours,
            datetime.now().isoformat()
        ))

        doctor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return doctor_id

    def get_doctor(self, doctor_id: int) -> Optional[Doctor]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_doctor(row)
        return None

    def get_doctor_by_email(self, email: str) -> Optional[Doctor]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM doctors WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_doctor(row)
        return None

    def get_all_doctors(self, active_only=True) -> List[Doctor]:
        conn = self.get_connection()
        cursor = conn.cursor()
        if active_only:
            cursor.execute('SELECT * FROM doctors WHERE is_active = 1 ORDER BY name')
        else:
            cursor.execute('SELECT * FROM doctors ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_doctor(row) for row in rows]

    def get_doctors_by_specialty(self, specialty: str) -> List[Doctor]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM doctors WHERE specialty = ? AND is_active = 1 ORDER BY name',
            (specialty,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_doctor(row) for row in rows]

    def update_doctor(self, doctor: Doctor) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE doctors SET name=?, email=?, phone=?, age=?, specialty=?,
                             is_active=?, max_patients=?, consultation_fee=?,
                             available_days=?, available_hours=?
            WHERE id=?
        ''', (
            doctor.name, doctor.email, doctor.phone, doctor.age, doctor.specialty,
            1 if doctor.is_active else 0, doctor.max_patients, doctor.consultation_fee,
            doctor.available_days, doctor.available_hours, doctor.id
        ))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_doctor(self, doctor_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE doctors SET is_active = 0 WHERE id = ?', (doctor_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def authenticate_doctor(self, email: str, password: str) -> Optional[Doctor]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM doctors WHERE email = ? AND is_active = 1', (email,))
        row = cursor.fetchone()
        conn.close()
        if row and self.verify_password(password, row['password_hash']):
            return self._row_to_doctor(row)
        return None

    def get_doctor_patient_count(self, doctor_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patients WHERE assigned_doctor_id = ?', (doctor_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def search_doctors(self, query: str) -> List[Doctor]:
        conn = self.get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM doctors 
            WHERE (name LIKE ? OR specialty LIKE ?) AND is_active = 1
            ORDER BY name
        ''', (search_term, search_term))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_doctor(row) for row in rows]

    # Patient
    def add_patient(self, patient: Patient) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patients (name, email, phone, age, patient_number, disease,
                                assigned_doctor_id, medical_history, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient.name, patient.email, patient.phone, patient.age,
            patient.patient_number, patient.disease, patient.assigned_doctor_id,
            patient.medical_history, "", datetime.now().isoformat()
        ))
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return patient_id

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients WHERE id = ?', (patient_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_patient(row)
        return None

    def get_patient_by_email(self, email: str) -> Optional[Patient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_patient(row)
        return None

    def get_all_patients(self) -> List[Patient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_patient(row) for row in rows]

    def get_patients_by_disease(self, disease: str) -> List[Patient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients WHERE disease LIKE ? ORDER BY name', (f"%{disease}%",))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_patient(row) for row in rows]

    def get_patients_by_doctor(self, doctor_id: int) -> List[Patient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients WHERE assigned_doctor_id = ? ORDER BY name', (doctor_id,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_patient(row) for row in rows]

    def update_patient(self, patient: Patient) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE patients SET name=?, email=?, phone=?, age=?, disease=?,
                              assigned_doctor_id=?, medical_history=?
            WHERE id=?
        ''', (
            patient.name, patient.email, patient.phone, patient.age,
            patient.disease, patient.assigned_doctor_id, patient.medical_history,
            patient.id
        ))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_patient(self, patient_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def search_patients(self, query: str) -> List[Patient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM patients 
            WHERE name LIKE ? OR email LIKE ? OR disease LIKE ?
            ORDER BY name
        ''', (search_term, search_term, search_term))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_patient(row) for row in rows]

    def search_patients_by_doctor(self, doctor_id: int, query: str) -> List[Patient]:
        """Search patients assigned to a specific doctor."""
        conn = self.get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM patients 
            WHERE assigned_doctor_id = ? AND (name LIKE ? OR email LIKE ? OR disease LIKE ?)
            ORDER BY name
        ''', (doctor_id, search_term, search_term, search_term))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_patient(row) for row in rows]

    def authenticate_patient(self, email: str, password: str) -> Optional[Patient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        if row and row['password_hash'] and self.verify_password(password, row['password_hash']):
            return self._row_to_patient(row)
        return None

    # Appoitments

    def add_appointment(self, appointment: Appointment) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, appointment_date,
                                     appointment_time, status, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            appointment.patient_id, appointment.doctor_id,
            appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            appointment.appointment_time, appointment.status, appointment.notes,
            datetime.now().isoformat()
        ))
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return appointment_id

    def get_appointment(self, appointment_id: int) -> Optional[Appointment]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialty as doctor_specialty
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.id = ?
        ''', (appointment_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_appointment(row)
        return None

    def get_appointments_by_patient(self, patient_id: int) -> List[Appointment]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, d.specialty as doctor_specialty
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_appointment(row) for row in rows]

    def get_appointments_by_doctor(self, doctor_id: int, status_filter: str = None) -> List[Appointment]:
        #Get appointments for a specific doctor
        conn = self.get_connection()
        cursor = conn.cursor()

        if status_filter and status_filter != "all":
            cursor.execute('''
                SELECT a.*, p.name as patient_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE a.doctor_id = ? AND a.status = ?
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            ''', (doctor_id, status_filter))
        else:
            cursor.execute('''
                SELECT a.*, p.name as patient_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE a.doctor_id = ?
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            ''', (doctor_id,))

        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_appointment(row) for row in rows]

    def get_all_appointments(self, status_filter: str = None) -> List[Appointment]:
        #Get all appointments
        conn = self.get_connection()
        cursor = conn.cursor()

        if status_filter and status_filter != "all":
            cursor.execute('''
                SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialty as doctor_specialty
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.status = ?
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            ''', (status_filter,))
        else:
            cursor.execute('''
                SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialty as doctor_specialty
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            ''')

        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_appointment(row) for row in rows]

    def update_appointment(self, appointment: Appointment) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE appointments 
            SET doctor_id=?, appointment_date=?, appointment_time=?, status=?, notes=?
            WHERE id=?
        ''', (
            appointment.doctor_id,
            appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            appointment.appointment_time, appointment.status, appointment.notes, appointment.id
        ))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def update_appointment_status(self, appointment_id: int, status: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, appointment_id))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_appointment(self, appointment_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def cancel_appointment(self, appointment_id: int) -> bool:
        return self.update_appointment_status(appointment_id, 'cancelled')

    def is_time_slot_available(self, doctor_id: int, date: datetime, time: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        date_str = date.strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE doctor_id = ? AND date(appointment_date) = ? AND appointment_time = ? AND status != 'cancelled'
        ''', (doctor_id, date_str, time))
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0

    def get_booked_slots(self, doctor_id: int, date: datetime) -> List[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        date_str = date.strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT appointment_time FROM appointments 
            WHERE doctor_id = ? AND date(appointment_date) = ? AND status != 'cancelled'
        ''', (doctor_id, date_str))
        rows = cursor.fetchall()
        conn.close()
        return [row['appointment_time'] for row in rows]

    def get_upcoming_appointments(self, patient_id: int, limit: int = 5) -> List[Appointment]:
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, d.specialty as doctor_specialty
            FROM appointments a JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = ? AND date(a.appointment_date) >= ? AND a.status = 'scheduled'
            ORDER BY a.appointment_date ASC, a.appointment_time ASC LIMIT ?
        ''', (patient_id, today, limit))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_appointment(row) for row in rows]

    def get_past_appointments(self, patient_id: int, limit: int = 10) -> List[Appointment]:
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, d.specialty as doctor_specialty
            FROM appointments a JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = ? AND (date(a.appointment_date) < ? OR a.status IN ('completed', 'cancelled'))
            ORDER BY a.appointment_date DESC, a.appointment_time DESC LIMIT ?
        ''', (patient_id, today, limit))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_appointment(row) for row in rows]

    # Stats

    def get_statistics(self) -> dict:
        """Get system-wide statistics (for admin)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        stats = {}

        cursor.execute('SELECT COUNT(*) FROM doctors WHERE is_active = 1')
        stats['total_doctors'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM patients')
        stats['total_patients'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE status = "scheduled"')
        stats['pending_appointments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE status = "completed"')
        stats['completed_appointments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments')
        stats['total_appointments'] = cursor.fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE date(appointment_date) = ? AND status = "scheduled"', (today,))
        stats['today_appointments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM admins WHERE is_active = 1')
        stats['total_admins'] = cursor.fetchone()[0]

        conn.close()
        return stats

    def get_patient_statistics(self, patient_id: int) -> dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        stats = {}

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE patient_id = ? AND status = "scheduled"', (patient_id,))
        stats['upcoming_appointments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE patient_id = ? AND status = "completed"', (patient_id,))
        stats['completed_appointments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE patient_id = ?', (patient_id,))
        stats['total_appointments'] = cursor.fetchone()[0]

        conn.close()
        return stats

    def get_doctor_statistics(self, doctor_id: int) -> dict:
        """Get statistics for a specific doctor."""
        conn = self.get_connection()
        cursor = conn.cursor()
        stats = {}

        cursor.execute('SELECT COUNT(*) FROM patients WHERE assigned_doctor_id = ?', (doctor_id,))
        stats['total_patients'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ? AND status = "scheduled"', (doctor_id,))
        stats['upcoming_appointments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ? AND status = "completed"', (doctor_id,))
        stats['completed_appointments'] = cursor.fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ? AND date(appointment_date) = ? AND status = "scheduled"', (doctor_id, today))
        stats['today_appointments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ?', (doctor_id,))
        stats['total_appointments'] = cursor.fetchone()[0]

        conn.close()
        return stats

    # Helpers

    def _row_to_admin(self, row) -> Admin:
        # Convert database row to Admin object
        return Admin(
            id=row['id'],
            name=row['name'],
            email=row['email'],
            password_hash=row['password_hash'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    def _row_to_doctor(self, row) -> Doctor:
        return Doctor(
            id=row['id'], name=row['name'], email=row['email'],
            phone=row['phone'] or "", age=row['age'] or 0,
            doctor_number=row['doctor_number'] or "", specialty=row['specialty'] or "",
            password_hash=row['password_hash'] or "", is_active=bool(row['is_active']),
            max_patients=row['max_patients'] or 20, consultation_fee=row['consultation_fee'] or 0.0,
            available_days=row['available_days'] or "Mon,Tue,Wed,Thu,Fri",
            available_hours=row['available_hours'] or "09:00-17:00",
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    def _row_to_patient(self, row) -> Patient:
        return Patient(
            id=row['id'], name=row['name'], email=row['email'],
            phone=row['phone'] or "", age=row['age'] or 0,
            patient_number=row['patient_number'] or "", disease=row['disease'] or "",
            assigned_doctor_id=row['assigned_doctor_id'], medical_history=row['medical_history'] or "",
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    def _row_to_appointment(self, row) -> Appointment:
        appt = Appointment(
            id=row['id'], patient_id=row['patient_id'], doctor_id=row['doctor_id'],
            appointment_date=datetime.fromisoformat(row['appointment_date']) if row['appointment_date'] else None,
            appointment_time=row['appointment_time'] or "", status=row['status'] or "scheduled",
            notes=row['notes'] or "",
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
        if 'patient_name' in row.keys():
            appt.patient_name = row['patient_name']
        if 'doctor_name' in row.keys():
            appt.doctor_name = row['doctor_name']
        if 'doctor_specialty' in row.keys():
            appt.doctor_specialty = row['doctor_specialty']
        return appt

    def seed_demo_data(self):
        #Seed demo data if database is empty
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if admins table has data
        cursor.execute('SELECT COUNT(*) FROM admins')
        admin_count = cursor.fetchone()[0]

        # Check if doctors table has data
        cursor.execute('SELECT COUNT(*) FROM doctors')
        doctor_count = cursor.fetchone()[0]

        if admin_count > 0 and doctor_count > 0:
            conn.close()
            return

        # Seed Admins
        if admin_count == 0:
            demo_admins = [
                Admin(
                    name="System Administrator",
                    email="admin@admin.com",
                    password_hash=self.hash_password("adminadmin"),
                    is_active=True
                ),
            ]
            for admin in demo_admins:
                self.add_admin(admin)

        # Seed Docs
        if doctor_count == 0:
            demo_doctors = [
                # Dr. Jihan (1 Doctor)
                Doctor(
                    name="Dr. Jihan Doctor",
                    email="jihan@demo.com",
                    phone="+1234567899",
                    age=35,
                    doctor_number="DOC000",
                    specialty="General Practice",
                    password_hash=self.hash_password("jihanjihan"),
                    consultation_fee=100.0
                )
            ]

            for doctor in demo_doctors:
                self.add_doctor(doctor)

            # Seed Pats
            # 1 Pat
            demo_patients = [
                Patient(name="Ahmad Al-Ali", email="ahmad.ali@email.com", phone="+963956789012",
                       age=35, patient_number="PAT001", disease="Hypertension", assigned_doctor_id=1)
            ]

            for patient in demo_patients:
                self.add_patient(patient)

            # Seed Apoits
            # No Apoits
            pass

        conn.close()

    def reset_database(self):
        #Reset DB
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM appointments')
        cursor.execute('DELETE FROM patients')
        cursor.execute('DELETE FROM doctors')
        cursor.execute('DELETE FROM admins')
        conn.commit()
        conn.close()
        self.clear_session()
        self.seed_demo_data()