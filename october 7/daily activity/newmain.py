from fastapi import FastAPI

app = FastAPI()

#----GET----
@app.get("/students")
def get_students():
    return {"This is a GET request"}

#----POST----
@app.post("/students")
def create_student():
    return {"This is a POST request"}

#----PUT----
@app.put("/students")
def update_student():
    return {"This is a PUT request"}

#----DELETE----
@app.delete("/students")
def delete_student():
    return {"This is a DELETE request"}