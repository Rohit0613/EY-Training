from fastapi.testclient import TestClient
from courses_api import app
import pytest
client = TestClient(app)

# Task 1
def test_add_course():
    course = {
        "id": 2, "title": "Python Medium", "duration": 60, "fee": 3500, "is_active": True
    }
    response = client.post("/courses", json=course)
    assert response.status_code == 201
    assert response.json() == course

def test_add_duplicate_course():
    course = {
        "id": 1, "title": "Python Basics", "duration": 30, "fee": 3000, "is_active": True
    }
    response = client.post("/courses", json=course)
    assert response.status_code == 400
    assert response.json()["detail"] == "Course ID already exists"

# Task 2
@pytest.mark.parametrize("course,code,text", [
    ({"id": 1, "title": "Python Basics", "duration": 30, "fee": 3000, "is_active": True}, 400,
     "Course ID already exists"),
    ({"id": 2, "title": "Python Medium", "duration": 60, "fee": 3500, "is_active": True}, 400,
     "Course ID already exists"),
    ({"id": 3, "title": "Python Advance", "duration": 180, "fee": 4000, "is_active": True}, 201, None)
])
def test_multiple_add_course(course, code, text):
    response = client.post("/courses", json=course)
    assert response.status_code == code
    if code == 201:
        assert response.json() == course
    else:
        assert response.json()["detail"] == text

# Task 3

def test_validation_error_add():
    course = {
        "id": 2, "title": "AI", "duration": 0, "fee": -500, "is_active": True
    }
    response = client.post("/courses", json=course)
    assert response.status_code == 422
    assert "Input should be greater than 0" in response.text


# Task 4

def test_check_fields_and_types():
    response = client.get("/courses")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list)
    assert all("id" in course for course in data)
    assert all("title" in course for course in data)
    assert all("duration" in course for course in data)
    assert all("fee" in course for course in data)
    assert all("is_active" in course for course in data)
