import json
import logging

logging.basicConfig(filename="task1_app.log",level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

data=[
{"name": "Rahul", "age": 21, "course": "AI", "marks": 85},
{"name": "Priya", "age": 22, "course": "ML", "marks": 90},
{"name": "Aniket", "age": 21, "course": "AI", "marks": 98},
{"name": "soham", "age": 20, "course": "ML", "marks":89}
]
with open("data.json","w") as f:
    json.dump(data,f,indent=4)
    logging.info("Data written")

print(data)
logging.info("Data displayed")

new_data=[{
    "name": "arjun",
    "age": 20,
    "course": "Data Science",
    "marks":78
}]
data.extend(new_data)
with open("data.json","w") as f:
    json.dump(data,f,indent=4)
    logging.info("new Data updated to json")
logging.info("json Data saved")

