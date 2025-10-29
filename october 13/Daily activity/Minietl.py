import pandas as pd

df=pd.read_csv("Student.csv")


df.dropna(inplace= True)
df['Marks']=df['Marks'].astype(int)
df['Results']=df['Marks'].apply (lambda x: "pass" if x > 0 else "fail")

df.to_csv("Cleaned_csv",index=False)
df=pd.read_csv("Student.csv")

print("Data Pipeline is completed. Cleaned data save to new csv")