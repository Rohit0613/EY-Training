from fastapi import APIRouter
import logging

router = APIRouter()

# In-memory visit counter
visit_count = 0

@router.get("/visits")
def count_visits():
    global visit_count
    visit_count += 1
    logging.info(f"Website visited {visit_count} times.")
    return {"visit_count": visit_count}