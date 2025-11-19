use university

db.teacher.drop()

db.teacher.insertMany([
  { id: 1, name: "Anita", subject: "Mathematics", salary: 55000 },
  { id: 2, name: "Ravi", subject: "Physics", salary: 60000 },
  { id: 3, name: "Sunita", subject: "English", salary: 52000 },
  { id: 4, name: "Amit", subject: "Computer Science", salary: 65000 },
  { id: 5, name: "Neha", subject: "Chemistry", salary: 58000 }
])

db.teacher.find()

db.teacher.findOne({ subject: "Physics" })

db.teacher.updateOne(
  { id: 3 },
  { $lt: { salary: 45000 } }
)

db.teacher.findOne({ id: 3 })

db.teacher.deleteOne({ id: 5 })

db.teacher.find()
