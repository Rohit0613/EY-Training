from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app=FastAPI()

class Employee(BaseModel):
    id: int
    name: str
    department: str
    Salary: float


Employees=[{"id": 1, "name": "Prajakta", "department": "HR", "Salary": 50000},]

@app.get("/employees")
def get_all_employee():
    return Employees

@app.post("/employees",status_code=201)
def add_employee(employee: Employee):
    Employees.append(employee.dict())
    return employee

@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    for emp in Employees:
        if emp["id"] == employee_id:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found")

