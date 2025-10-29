from celery import Celery
from Environment import engine  # SQLAlchemy engine
from etl import run_etl
import pandas as pd
from sqlalchemy import text

celery = Celery('tasks', broker='amqp://guest:guest@localhost:5672//')

@celery.task
def process_visit_record(visit_json):

    try:
        # Insert visit into visits table
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO visits (VisitID, PatientID, DoctorID, Date, Cost)
                VALUES (:vid, :pid, :did, :date, :cost)
            """), {
                "vid": visit_json["VisitID"],
                "pid": visit_json["PatientID"],
                "did": visit_json["DoctorID"],
                "date": visit_json["Date"],
                "cost": visit_json["Cost"]
            })

        # Run ETL
        run_etl()

        return {"status": "success", "visit_id": visit_json["VisitID"]}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
