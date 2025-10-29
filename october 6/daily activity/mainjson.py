import json

#python dictionary

Student ={
    "name": "rahul",
    "age": 22,
    "courses":["AI","ML"],
    "marks":{"AI": 85,"ML": 75}
}

with open("Student.json","w") as f:
    json.dump(Student, f,indent=4)


with open("Student.json","r") as f:
    data=json.load(f)


print(data["name"])
print(data["marks"]["AI"])
