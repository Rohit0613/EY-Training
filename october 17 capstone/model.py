from sqlalchemy import Table, Column, String, Integer, Date, DECIMAL, ForeignKey, MetaData

metadata = MetaData()

patients = Table(
    "patients", metadata,
    Column("PatientID", String(10), primary_key=True),
    Column("Name", String(50)),
    Column("Age", Integer),
    Column("Condition", String(50))
)

doctors = Table(
    "doctors", metadata,
    Column("DoctorID", String(10), primary_key=True),
    Column("Name", String(50)),
    Column("Specialization", String(50))
)

visits = Table(
    "visits", metadata,
    Column("VisitID", String(10), primary_key=True),
    Column("PatientID", String(10), ForeignKey("patients.PatientID")),
    Column("DoctorID", String(10), ForeignKey("doctors.DoctorID")),
    Column("Date", Date),
    Column("Cost", DECIMAL(10,2))
)
