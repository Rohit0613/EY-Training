from fastapi import FastAPI ,HTTPException
from pydantic import BaseModel
app = FastAPI()

#Pydantic model for validation

class Student(BaseModel):
    id:int
    name: str
    age: int
    course: str

#In-memory "database"
students = [
    {"sid":0,"name":"Anushka","age":22,"course":"AI"},
    {"sid":1,"name":"Prajakta","age":20,"course":"ML"},
]

@app.get("/students")
def get_all_student():
    return {"students ": students}

@app.get("/students/{student_id}")
def get_student(student_id: int):
    for s in students:
        if s["sid"] == student_id:
            return {"student_id":students[student_id]['sid'],"name":students[student_id]["name"],"course":students[student_id]["course"]}
    raise HTTPException(status_code=404, detail="Student not found")


# ----- POST-----

@app.post("/students",status_code=201)
def add_student(student: Student):
    students.append(student.dict())
    return{"message":"Student added successfully","student":student}


#----- PUT -----
@app.put("/students/{student_id}")
def update_student(student_id: int,updated_student: Student):
    for i,s in enumerate(students):
        if s["sid"] == student_id:
            students[i] = updated_student.dict()
            return {"message":"Student updated","student":updated_student}
    raise HTTPException(status_code=404, detail="Student not found")

#----- DELETE -----
@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    for i,s in enumerate(students):
        if s["sid"] == student_id:
            deleted_stud = students.pop(i)
            return {"message":"Student deleted","student":deleted_stud}
    raise HTTPException(status_code=404, detail="Student not found")