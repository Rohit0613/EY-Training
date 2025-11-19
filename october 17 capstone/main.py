from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from Environment import engine

app = FastAPI(title="Patient Health Records API")

# ==============================================================
# ================ PATIENT ROUTES ===============================
# ==============================================================

@app.get("/patients")
def get_patients():
    """Get all patients"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM patients"))
        return [dict(row) for row in result]


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    """Get one patient by ID"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM patients WHERE PatientID=:pid"), {"pid": patient_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Patient not found")
        return dict(result)


@app.post("/patients")
def add_patient(payload: dict):
    """Add a new patient"""
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO patients (PatientID, Name, Age, Gender, Condition)
                VALUES (:id, :name, :age, :gender, :cond)
            """), {
                "id": payload["PatientID"],
                "name": payload["Name"],
                "age": payload["Age"],
                "gender": payload["Gender"],
                "cond": payload["Condition"]
            })
        return {"status": "Patient added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, payload: dict):
    """Update a patient record"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE patients 
                SET Name=:name, Age=:age, Gender=:gender, Condition=:cond
                WHERE PatientID=:id
            """), {
                "id": patient_id,
                "name": payload["Name"],
                "age": payload["Age"],
                "gender": payload["Gender"],
                "cond": payload["Condition"]
            })
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Patient not found")
        return {"status": "Patient updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str):
    """Delete a patient record"""
    with engine.begin() as conn:
        result = conn.execute(text("DELETE FROM patients WHERE PatientID=:id"), {"id": patient_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "Patient deleted successfully"}


# ==============================================================
# ================ DOCTOR ROUTES ================================
# ==============================================================

@app.get("/doctors")
def get_doctors():
    """Get all doctors"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM doctors"))
        return [dict(row) for row in result]


@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    """Get one doctor by ID"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM doctors WHERE DoctorID=:did"), {"did": doctor_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return dict(result)


@app.post("/doctors")
def add_doctor(payload: dict):
    """Add a new doctor"""
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO doctors (DoctorID, Name, Specialization)
                VALUES (:id, :name, :spec)
            """), {
                "id": payload["DoctorID"],
                "name": payload["Name"],
                "spec": payload["Specialization"]
            })
        return {"status": "Doctor added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/doctors/{doctor_id}")
def update_doctor(doctor_id: str, payload: dict):
    """Update a doctor's details"""
    with engine.begin() as conn:
        result = conn.execute(text("""
            UPDATE doctors 
            SET Name=:name, Specialization=:spec
            WHERE DoctorID=:id
        """), {
            "id": doctor_id,
            "name": payload["Name"],
            "spec": payload["Specialization"]
        })
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Doctor not found")
    return {"status": "Doctor updated successfully"}


@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: str):
    """Delete a doctor"""
    with engine.begin() as conn:
        result = conn.execute(text("DELETE FROM doctors WHERE DoctorID=:id"), {"id": doctor_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Doctor not found")
    return {"status": "Doctor deleted successfully"}


# ==============================================================
# ================ VISIT ROUTES =================================
# ==============================================================

@app.get("/visits")
def get_visits():
    """Get all visits"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM visits"))
        return [dict(row) for row in result]


@app.get("/visits/{visit_id}")
def get_visit(visit_id: str):
    """Get one visit"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM visits WHERE VisitID=:vid"), {"vid": visit_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Visit not found")
        return dict(result)

@app.post("/visits")
def add_visit(payload: dict):
    """Add a new visit"""
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO visits (VisitID, PatientID, DoctorID, Date, Cost)
                VALUES (:vid, :pid, :did, :date, :cost)
            """), {
                "vid": payload["VisitID"],
                "pid": payload["PatientID"],
                "did": payload["DoctorID"],
                "date": payload["Date"],
                "cost": payload["Cost"]
            })
        return {"status": "Visit added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/visits/{visit_id}")
def update_visit(visit_id: str, payload: dict):
    """Update visit details"""
    with engine.begin() as conn:
        result = conn.execute(text("""
            UPDATE visits 
            SET PatientID=:pid, DoctorID=:did, Date=:date, Cost=:cost
            WHERE VisitID=:vid
        """), {
            "vid": visit_id,
            "pid": payload["PatientID"],
            "did": payload["DoctorID"],
            "date": payload["Date"],
            "cost": payload["Cost"]
        })
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Visit not found")
    return {"status": "Visit updated successfully"}


@app.delete("/visits/{visit_id}")
def delete_visit(visit_id: str):
    """Delete a visit record"""
    with engine.begin() as conn:
        result = conn.execute(text("DELETE FROM visits WHERE VisitID=:id"), {"id": visit_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Visit not found")
    return {"status": "Visit deleted successfully"}


@app.get("/")
def home():
    return {"message": "Welcome to Patient Health Records API"}
