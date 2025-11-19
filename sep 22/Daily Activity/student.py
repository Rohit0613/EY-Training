Student={
    "Name": "Rohit",
    "Age": 22,
    "course": "AI & DS"
}

print(Student["Name"]) # Access By Key
print(Student.get("Age"))

Student["grade"]="A"
Student['Age']=23 #update existing key

print(Student)

Student.pop("course") #remove by key
del Student["grade"] # delete key

print(Student)