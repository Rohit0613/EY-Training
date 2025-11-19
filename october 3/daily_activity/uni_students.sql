use university

db.student.drop()

db.student.insertOne({
  id: 1,
  name: "Rahul",
  age: 20,
  course: "B.Tech",
  marks: 75
})

db.student.insertMany([
  { id: 2, name: "Priya", age: 21, course: "B.Sc", marks: 68 },
  { id: 3, name: "Aman", age: 22, course: "B.Com", marks: 80 },
  { id: 4, name: "Kiran", age: 19, course: "BBA", marks: 72 },
  { id: 5, name: "Vikas", age: 23, course: "BCA", marks: 65 }
])

db.student.find()

db.student.updateOne(
  { id: 2 },
  { $set: { marks: 73 } }
)

db.student.updateMany(
  { marks: { $lt: 70 } },
  { $inc: { marks: 5 } }
)

db.student.deleteOne({ id: 5 })

db.student.deleteMany({ age: { $gt: 22 } })

db.student.find()
