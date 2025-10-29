from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

students = [
    {"id": 1, "name": "Rohit", "age": 22, "grade": "A"},
    {"id": 2, "name": "Prajakta", "age": 21, "grade": "B+"},
    {"id": 3, "name": "Aarav", "age": 23, "grade": "A"},
    {"id": 4, "name": "Meera", "age": 20, "grade": "A-"},
    {"id": 5, "name": "Karan", "age": 22, "grade": "B"},
]

@app.get("/", response_class=HTMLResponse)
def home_page(request: Request, show: bool = False):
    data = students if show else None
    return templates.TemplateResponse("index.html", {"request": request, "students": data})
