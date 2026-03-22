from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

doctors = [
    {"id": 1, "name": "Dr Sharma", "specialization": "Cardiologist", "fee": 500, "experience_years": 10, "is_available": True},
    {"id": 2, "name": "Dr Kumar", "specialization": "Dermatologist", "fee": 400, "experience_years": 8, "is_available": True},
    {"id": 3, "name": "Dr Reddy", "specialization": "Pediatrician", "fee": 300, "experience_years": 5, "is_available": False},
    {"id": 4, "name": "Dr Rao", "specialization": "General", "fee": 200, "experience_years": 6, "is_available": True},
    {"id": 5, "name": "Dr Mehta", "specialization": "Cardiologist", "fee": 600, "experience_years": 12, "is_available": True},
    {"id": 6, "name": "Dr Singh", "specialization": "Dermatologist", "fee": 350, "experience_years": 7, "is_available": False}
]

appointments = []
appt_counter = 1


@app.get("/")
def home():
    return {"message": "Welcome to MediCare Clinic"}


@app.get("/doctors")
def get_doctors():
    total = len(doctors)
    available = len([d for d in doctors if d["is_available"]])
    return {"total": total, "available_count": available, "data": doctors}


@app.get("/doctors/summary")
def summary():
    total = len(doctors)
    available = len([d for d in doctors if d["is_available"]])
    most_exp = max(doctors, key=lambda x: x["experience_years"])
    cheapest = min(doctors, key=lambda x: x["fee"])
    spec_count = {}
    for d in doctors:
        spec = d["specialization"]
        spec_count[spec] = spec_count.get(spec, 0) + 1
    return {
        "total": total,
        "available": available,
        "most_experienced": most_exp["name"],
        "cheapest_fee": cheapest["fee"],
        "specializations": spec_count
    }


@app.get("/doctors/filter")
def filter_doctors(
    specialization: Optional[str] = None,
    max_fee: Optional[int] = None,
    min_experience: Optional[int] = None,
    is_available: Optional[bool] = None
):
    result = doctors

    if specialization is not None:
        result = [d for d in result if d["specialization"] == specialization]

    if max_fee is not None:
        result = [d for d in result if d["fee"] <= max_fee]

    if min_experience is not None:
        result = [d for d in result if d["experience_years"] >= min_experience]

    if is_available is not None:
        result = [d for d in result if d["is_available"] == is_available]

    return {"total": len(result), "data": result}


@app.get("/doctors/search")
def search_doctors(keyword: str):
    result = []
    for d in doctors:
        if keyword.lower() in d["name"].lower() or keyword.lower() in d["specialization"].lower():
            result.append(d)

    if not result:
        return {"message": "No doctors found"}

    return {"total_found": len(result), "data": result}


@app.get("/doctors/sort")
def sort_doctors(sort_by: str = "fee"):
    if sort_by not in ["fee", "name", "experience_years"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    sorted_list = sorted(doctors, key=lambda x: x[sort_by])
    return {"sorted_by": sort_by, "data": sorted_list}


@app.get("/doctors/page")
def paginate_doctors(page: int = 1, limit: int = 3):
    total = len(doctors)
    start = (page - 1) * limit
    end = start + limit
    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "data": doctors[start:end]
    }


@app.get("/doctors/browse")
def browse_doctors(
    keyword: str = "",
    sort_by: str = "fee",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = doctors

    if keyword:
        result = [d for d in result if keyword.lower() in d["name"].lower() or keyword.lower() in d["specialization"].lower()]

    reverse = True if order == "desc" else False

    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    start = (page - 1) * limit
    end = start + limit

    return {
        "total": len(result),
        "page": page,
        "data": result[start:end]
    }


@app.get("/appointments")
def get_appointments():
    return {"total": len(appointments), "data": appointments}


@app.get("/appointments/active")
def active_appointments():
    result = [a for a in appointments if a["status"] in ["scheduled", "confirmed"]]
    return {"total": len(result), "data": result}


@app.get("/appointments/search")
def search_appointments(patient_name: str):
    result = [a for a in appointments if patient_name.lower() in a["patient"].lower()]
    return {"total": len(result), "data": result}


@app.get("/appointments/sort")
def sort_appointments(sort_by: str = "date"):
    if sort_by not in ["fee", "date"]:
        raise HTTPException(status_code=400, detail="Invalid field")

    key = "final_fee" if sort_by == "fee" else "date"
    return sorted(appointments, key=lambda x: x[key])


@app.get("/appointments/page")
def paginate_appointments(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    return appointments[start:end]


class AppointmentRequest(BaseModel):
    patient_name: str = Field(min_length=2)
    doctor_id: int = Field(gt=0)
    date: str = Field(min_length=8)
    reason: str = Field(min_length=5)
    appointment_type: str = "in-person"
    senior_citizen: bool = False


def find_doctor(doctor_id):
    for d in doctors:
        if d["id"] == doctor_id:
            return d


def calculate_fee(base_fee, appointment_type, senior):
    if appointment_type == "video":
        fee = base_fee * 0.8
    elif appointment_type == "emergency":
        fee = base_fee * 1.5
    else:
        fee = base_fee

    original_fee = fee

    if senior:
        fee = fee * 0.85

    return int(original_fee), int(fee)


@app.post("/appointments")
def create_appointment(a: AppointmentRequest):
    global appt_counter

    doctor = find_doctor(a.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not doctor["is_available"]:
        raise HTTPException(status_code=400, detail="Doctor not available")

    original_fee, final_fee = calculate_fee(
        doctor["fee"], a.appointment_type, a.senior_citizen
    )

    new_appointment = {
        "appointment_id": appt_counter,
        "patient": a.patient_name,
        "doctor": doctor["name"],
        "doctor_id": doctor["id"],
        "date": a.date,
        "type": a.appointment_type,
        "original_fee": original_fee,
        "final_fee": final_fee,
        "status": "scheduled"
    }

    appointments.append(new_appointment)
    appt_counter += 1

    doctor["is_available"] = False

    return new_appointment


class NewDoctor(BaseModel):
    name: str = Field(min_length=2)
    specialization: str = Field(min_length=2)
    fee: int = Field(gt=0)
    experience_years: int = Field(gt=0)
    is_available: bool = True


@app.post("/doctors", status_code=201)
def add_doctor(d: NewDoctor):
    for doc in doctors:
        if doc["name"] == d.name:
            raise HTTPException(status_code=400, detail="Doctor already exists")

    new_id = max([doc["id"] for doc in doctors]) + 1

    new_doc = {
        "id": new_id,
        "name": d.name,
        "specialization": d.specialization,
        "fee": d.fee,
        "experience_years": d.experience_years,
        "is_available": d.is_available
    }

    doctors.append(new_doc)
    return new_doc


@app.put("/doctors/{doctor_id}")
def update_doctor(
    doctor_id: int,
    fee: Optional[int] = None,
    is_available: Optional[bool] = None
):
    for d in doctors:
        if d["id"] == doctor_id:
            if fee is not None:
                d["fee"] = fee
            if is_available is not None:
                d["is_available"] = is_available
            return d

    raise HTTPException(status_code=404, detail="Doctor not found")


@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int):
    for d in doctors:
        if d["id"] == doctor_id:
            for a in appointments:
                if a["doctor_id"] == doctor_id and a["status"] == "scheduled":
                    raise HTTPException(status_code=400, detail="Doctor has active appointments")

            doctors.remove(d)
            return {"message": "Doctor deleted"}

    raise HTTPException(status_code=404, detail="Doctor not found")


@app.post("/appointments/{appointment_id}/confirm")
def confirm_appointment(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "confirmed"
            return a
    raise HTTPException(status_code=404, detail="Appointment not found")


@app.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "cancelled"

            for d in doctors:
                if d["id"] == a["doctor_id"]:
                    d["is_available"] = True

            return a
    raise HTTPException(status_code=404, detail="Appointment not found")


@app.post("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "completed"
            return a
    raise HTTPException(status_code=404, detail="Appointment not found")


@app.get("/appointments/by-doctor/{doctor_id}")
def appointments_by_doctor(doctor_id: int):
    result = [a for a in appointments if a["doctor_id"] == doctor_id]
    return {"total": len(result), "data": result}


@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    for d in doctors:
        if d["id"] == doctor_id:
            return d
    raise HTTPException(status_code=404, detail="Doctor not found")