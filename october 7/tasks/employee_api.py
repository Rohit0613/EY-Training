from fastapi import FastAPI ,HTTPException
from pydantic import BaseModel

app = FastAPI()

#Pydantic model for validation

class Employee(BaseModel):
    id:int
    name: str
    department: str
    salary: float

#In-memory "database"
employees = [
    {
    "id": 1,
    "name": "Ravi Kumar",
    "department": "HR",
    "salary": 80000
    },
    {
    "id": 2,
    "name": "Rushita Sharma",
    "department": "Finance",
    "salary": 60000
    },
]

@app.get("/employees")
def get_all_employees():
    return {"employees ": employees}

@app.get("/employees/count")
def get_emp_count():
    total_count = len(employees)
    return {"Total Employees": total_count}

@app.get("/employees/{emp_id}")
def get_employee(emp_id: int):
    for e in employees:
        if e["id"] == emp_id:
            return {"employee detail": e}
    raise HTTPException(status_code=404, detail="Employee not found")

# ----- POST-----

@app.post("/employees",status_code=201)
def add_employee(emp: Employee):
    for e in employees:
        if e["id"] == emp.id:
            raise HTTPException(status_code=400, detail="Employee ID already exists")

    employees.append(emp.dict())
    return{"message":"Employee added successfully","employee":emp}


# #----- PUT -----
@app.put("/employees/{emp_id}")
def update_employee(emp_id: int,updated_emp: Employee):
    for i,e in enumerate(employees):
        if e["id"] == emp_id:
            employees[i] = updated_emp.dict()
            return {"message":"Employee updated","student":updated_emp}
    raise HTTPException(status_code=404, detail="Employee not found")

# #----- DELETE -----
@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int):
    for i,e in enumerate(employees):
        if e["id"] == emp_id:
            deleted_emp = employees.pop(i)
            return {"message":"Employee deleted","Employee":deleted_emp}
    raise HTTPException(status_code=404, detail="Employee not found")

