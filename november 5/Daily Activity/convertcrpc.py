import pandas as pd
import json

# Try reading the CSV with 'ISO-8859-1' encoding to handle special characters
df = pd.read_csv("crpc_sections.csv", encoding='ISO-8859-1')  # Change to your actual file path

# Optionally, clean data if necessary (remove rows with missing values)
df = df.dropna(subset=["Chapter", "Section", "Section _name", "Description"])

# Convert to dictionary (list of records)
crpc_data = df.to_dict(orient="records")

# Save the data as JSON
with open("crpc_sections.json", "w", encoding="utf-8") as json_file:
    json.dump(crpc_data, json_file, ensure_ascii=False, indent=2)

print("? CrPC data converted to JSON successfully!")
