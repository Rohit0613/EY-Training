
import pandas as pd
from Environment import engine
import sys

def generate_kpis():
    try:
        # Read tables
        patients = pd.read_sql("SELECT * FROM patients", engine)
        doctors  = pd.read_sql("SELECT * FROM doctors", engine)
        visits   = pd.read_sql("SELECT * FROM visits", engine)

        # Ensure Date is datetime and Cost is numeric
        visits['Date'] = pd.to_datetime(visits['Date'], errors='coerce')
        visits['Cost'] = pd.to_numeric(visits['Cost'], errors='coerce')

        # Basic cleaning: fill missing IDs for safe grouping
        visits['PatientID'] = visits['PatientID'].astype(str).fillna('UNKNOWN')
        visits['DoctorID']  = visits['DoctorID'].astype(str).fillna('UNKNOWN')

        # ---- KPI 1: Average cost per visit ----
        avg_cost = float(visits['Cost'].mean(skipna=True)) if not visits['Cost'].dropna().empty else 0.0

        # ---- KPI 2: Most visited doctor ----
        doc_counts = visits.groupby('DoctorID').size().rename('visit_count').reset_index()
        if not doc_counts.empty:
            top_doc_row = doc_counts.sort_values('visit_count', ascending=False).iloc[0]
            top_doctor_id = top_doc_row['DoctorID']
            top_doctor_visits = int(top_doc_row['visit_count'])
            # get doctor's name if available
            doc_name_row = doctors[doctors['DoctorID'] == top_doctor_id]
            top_doctor_name = doc_name_row['Name'].iloc[0] if not doc_name_row.empty else "Unknown"
        else:
            top_doctor_id = None
            top_doctor_name = None
            top_doctor_visits = 0

        # ---- KPI 3: Number of visits per patient ----
        visits_per_patient = visits.groupby('PatientID').size().rename('visit_count').reset_index()
        # merge patient name if available
        visits_per_patient = visits_per_patient.merge(
            patients[['PatientID', 'Name']].rename(columns={'Name': 'PatientName'}),
            on='PatientID',
            how='left'
        )
        visits_per_patient['PatientName'] = visits_per_patient['PatientName'].fillna('Unknown')

        # ---- KPI 4: Monthly revenue ----
        visits['Month'] = visits['Date'].dt.to_period('M').astype(str)  # e.g. "2025-10"
        monthly_revenue = visits.groupby('Month')['Cost'].sum().reset_index().rename(columns={'Cost': 'Revenue'})
        # Sort months chronologically if possible
        try:
            monthly_revenue['Month_sort'] = pd.to_datetime(monthly_revenue['Month'], format='%Y-%m', errors='coerce')
            monthly_revenue = monthly_revenue.sort_values('Month_sort').drop(columns='Month_sort').reset_index(drop=True)
        except Exception:
            monthly_revenue = monthly_revenue.sort_values('Month').reset_index(drop=True)

        # ---- Additional useful totals ----
        total_visits = int(len(visits))
        total_revenue = float(monthly_revenue['Revenue'].sum()) if not monthly_revenue.empty else float(visits['Cost'].sum(skipna=True))

        # ---- Build summary table (one-row DataFrame) ----
        summary = pd.DataFrame([{
            'metric': 'average_cost_per_visit',
            'value': avg_cost
        }, {
            'metric': 'most_visited_doctor_id',
            'value': top_doctor_id
        }, {
            'metric': 'most_visited_doctor_name',
            'value': top_doctor_name
        }, {
            'metric': 'most_visited_doctor_visits',
            'value': top_doctor_visits
        }, {
            'metric': 'total_visits',
            'value': total_visits
        }, {
            'metric': 'total_revenue',
            'value': total_revenue
        }])

        # ---- Prepare DataFrames with section labels so single CSV is readable ----
        summary['section'] = 'summary'
        visits_per_patient_df = visits_per_patient[['PatientID', 'PatientName', 'visit_count']].copy()
        visits_per_patient_df['section'] = 'visits_per_patient'

        per_doctor_df = doc_counts.merge(doctors[['DoctorID','Name']].rename(columns={'Name':'DoctorName'}), on='DoctorID', how='left')
        per_doctor_df['DoctorName'] = per_doctor_df['DoctorName'].fillna('Unknown')
        per_doctor_df = per_doctor_df[['DoctorID','DoctorName','visit_count']]
        per_doctor_df['section'] = 'visits_per_doctor'

        monthly_df = monthly_revenue.copy()
        monthly_df['section'] = 'monthly_revenue'

        # Normalize column ordering by adding missing cols so concat is clean
        # Create a list of all columns used across DFs
        all_cols = ['section','metric','value','PatientID','PatientName','visit_count','DoctorID','DoctorName','Month','Revenue']
        def normalize(df):
            # ensure all columns exist
            for c in all_cols:
                if c not in df.columns:
                    df[c] = ""
            return df[all_cols]

        summary_norm = normalize(summary)
        visits_per_patient_norm = normalize(visits_per_patient_df)
        per_doctor_norm = normalize(per_doctor_df)
        monthly_norm = normalize(monthly_df.rename(columns={'Month':'Month','Revenue':'Revenue'}))

        # Concatenate in order and save
        report = pd.concat([summary_norm,
                            pd.DataFrame([["","","","","","","","","",""]], columns=all_cols),  # blank separator row
                            visits_per_patient_norm,
                            pd.DataFrame([["","","","","","","","","",""]], columns=all_cols),
                            per_doctor_norm,
                            pd.DataFrame([["","","","","","","","","",""]], columns=all_cols),
                            monthly_norm], ignore_index=True)

        report.to_csv('kpi_report.csv', index=False)
        print("kpi_report.csv written successfully.")
        return True

    except Exception as exc:
        print("Failed to generate KPI report:", exc, file=sys.stderr)
        return False

if __name__ == "__main__":
    generate_kpis()
