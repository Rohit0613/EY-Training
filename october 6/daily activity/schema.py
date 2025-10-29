from pydantic import BaseModel

class Student(BaseModel):
    name: str
    age: int
    email: str
    is_active: bool= True


# invalid_data= {"name":"John","age":"twentyfive","email":"johnny@gmail.com"}

data={"name":"John","age":25,"email":"johnny@gmail.com"}
student = Student(**data)

print(student)
print(student.name)

