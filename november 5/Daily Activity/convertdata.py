import pandas as pd
import json

# Load the CSV
df = pd.read_csv("ipc_sections.csv")
print(df.columns)
# Rename columns if needed (depends on your dataset)
# Example: adjust names to be consistent with your RAG pipeline
df = df.rename(columns={
    "Section": "section",
    "Offence": "title",
    "Description": "description",
    "Punishment": "punishment"
})

# Convert to list of dictionaries
records = df.to_dict(orient="records")

# Save as JSON
with open("ipc_sections.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"✅ Converted {len(records)} records to ipc_sections.json")