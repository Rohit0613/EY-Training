from fastapi.testclient import TestClient
from emain import app

client=TestClient(app)

def test_get_all_employees():
    response = client.get("/employees")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_add_employee():
    new_emp= {
        "name": "Neha Varma",
        "id": 2,
        "department": "it",
        "Salary": 60000
    }
    response = client.post("/employees", json= new_emp)
    assert response.status_code == 201
    assert response.json()["name"]== "Neha Varma"


def test_get_employee_by_id():
    response = client.get("/employees/1")
    assert response.status_code==200
    assert response.json()["name"]=="Prajakta"

def test_get_employee_not_found():
    response = client.get("/employees/11")
    assert response.status_code==404
    assert response.json()["detail"]=="Employee not found"