class student:
    def __init__(self,name,age,email):
        self.name=name
        self.age=age
        self.email=email


data1={"name":"John","age":25,"email":"johnnybaba@gmail.com"}
Student=student(**data1)
print(Student.age)