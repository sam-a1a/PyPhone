#OOP Models
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Person:
    #Base class for all persons
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    age: int = 0
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self):
        #Convert to Dic
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'age': self.age,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data):
        #Create from Dic
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class Patient(Person):
    #Pat class inheriting from Person
    patient_number: str = ""
    disease: str = ""
    assigned_doctor_id: Optional[int] = None
    medical_history: str = ""
    password_hash: str = ""

    def to_dict(self):
        #Convert to dic
        data = super().to_dict()
        data.update({
            'patient_number': self.patient_number,
            'disease': self.disease,
            'assigned_doctor_id': self.assigned_doctor_id,
            'medical_history': self.medical_history
        })
        # password_hash is deliberately left out, as it is on Admin
        return data

@dataclass
class Doctor(Person):
    #Doctor class inheriting from Person
    doctor_number: str = ""
    specialty: str = ""
    password_hash: str = ""
    is_active: bool = True
    max_patients: int = 20
    consultation_fee: float = 0.0
    available_days: str = "Mon,Tue,Wed,Thu,Fri"
    available_hours: str = "09:00-17:00"

    def to_dict(self):
        #Convert to dic
        data = super().to_dict()
        data.update({
            'doctor_number': self.doctor_number,
            'specialty': self.specialty,
            'password_hash': self.password_hash,
            'is_active': self.is_active,
            'max_patients': self.max_patients,
            'consultation_fee': self.consultation_fee,
            'available_days': self.available_days,
            'available_hours': self.available_hours
        })
        return data


@dataclass
class Appointment:
    #Appointment/Booking class
    id: Optional[int] = None
    patient_id: int = 0
    doctor_id: int = 0
    appointment_date: Optional[datetime] = None
    appointment_time: str = ""
    status: str = "scheduled"  # scheduled, completed, cancelled
    notes: str = ""
    created_at: Optional[datetime] = None

    # Joined data (not stored in DB)
    patient_name: str = ""
    doctor_name: str = ""
    doctor_specialty: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self):
        #Convert to dic
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_time': self.appointment_time,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Admin:
    #Admin class for sys ads
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Specialties
SPECIALTIES = [
    "General Practice",
    "Cardiology",
    "Dermatology",
    "Neurology",
    "Orthopedics",
    "Pediatrics",
    "Psychiatry",
    "Oncology",
    "Ophthalmology",
    "ENT",
    "Gynecology",
    "Urology",
    "Dentistry",
    "Surgery"
]

# Diseases
DISEASES = [
    "Diabetes",
    "Hypertension",
    "Heart Disease",
    "Asthma",
    "Arthritis",
    "Cancer",
    "Depression",
    "Anxiety",
    "Flu",
    "COVID-19",
    "Allergies",
    "Back Pain",
    "Migraine",
    "Other"
]