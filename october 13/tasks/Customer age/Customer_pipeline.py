import pandas as pd
from datetime import datetime

df=pd.read_csv("Customer.csv")
df['Agegroup']=df['Age'].apply (lambda x: "Young" if x<30 else("Adult" if 30<=x<50 else "Senior"))
newdf=df[df['Age']<=20]
newdf.to_csv("Filtered_Customer1.csv", index=False)
print(f"pipeline executed at {datetime.now()}")
