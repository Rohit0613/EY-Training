import os, sys
from datetime import datetime, timedelta
import pandas as pd
from Environment import engine   # your SQLAlchemy engine

OUT_DIR = "reports"
os.makedirs(OUT_DIR, exist_ok=True)

def target_date_from_arg():
    if len(sys.argv) > 1:
        return datetime.strptime(sys.argv[1], "%Y%m%d").date()
    return (datetime.now() - timedelta(days=1)).date()

def main():
    target = target_date_from_arg()
    fname = f"daily_visits_report_{target.strftime('%Y%m%d')}.csv"
    path = os.path.join(OUT_DIR, fname)

    sql = """
    SELECT v.VisitID, v.PatientID, p.Name AS PatientName,
           v.DoctorID, d.Name AS DoctorName,
           v.Date, v.Cost
    FROM visits v
    LEFT JOIN patients p ON v.PatientID = p.PatientID
    LEFT JOIN doctors d  ON v.DoctorID  = d.DoctorID
    WHERE DATE(v.Date) = :target_date
    ORDER BY v.Date
    """

    try:
        df = pd.read_sql(sql, engine, params={"target_date": target.isoformat()})
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce')
        df.to_csv(path, index=False)
        print(f"Report written: {path} (rows={len(df)})")
    except Exception as e:
        print(f"Failed to generate report for {target}")