import pandas as pd
from logger_config import logger
from Environment import engine

def run_etl():
    try:
        # Read tables from the database
        patients = pd.read_sql('SELECT * FROM patients', engine)
        doctors = pd.read_sql('SELECT * FROM doctors', engine)
        visits = pd.read_sql('SELECT * FROM visits', engine)

        # Merge tables
        df = visits.merge(patients, on='PatientID', how='left').merge(doctors, on='DoctorID', how='left')

        # Log missing DoctorID or PatientID
        missing_doctors = df['DoctorID'].isna().sum()
        missing_patients = df['PatientID'].isna().sum()
        if missing_doctors > 0:
            logger.error(f"ETL Error: {missing_doctors} visits with missing DoctorID")
        if missing_patients > 0:
            logger.error(f"ETL Error: {missing_patients} visits with missing PatientID")

        # Month column
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Month'] = df['Date'].dt.to_period('M').astype(str)

        # FollowUpRequired: patients who visited more than once
        vis_counts = df.groupby('PatientID')['VisitID'].nunique()
        df = df.merge(vis_counts.rename('visit_count'), on='PatientID')
        df['FollowUpRequired'] = df['visit_count'] > 1

        follow_up_count = int(df['FollowUpRequired'].sum())
        logger.info(f"ETL Info: {follow_up_count} patients require follow-up")

        df.to_csv('processed_visits.csv', index=False)
        return {"status": "ETL completed", "follow_up_count": follow_up_count}

    except Exception as e:
        logger.exception(f"ETL Exception: {e}")
        raise
