import numpy as np
import pandas as pd

data={
    "Name": ["John", "baby", "devil","Rohit","Aniket"],
    "Age":[22,23,24,25,26],
    "course":["AI","DATA SCIENCE","ML","IOT","DL"],
    "Marks":[40,60,90,55,88]
}

df=pd.DataFrame(data)
print(df)

print(df["Name"])  #single column
print(df[["Name", "Marks"]])  #multiple column
print(df.iloc[0])  #first row
print(df.loc[ 3,"Marks"]) #value at row 2,column marks

#filter data
highscore=df[df["Marks"]>66]
print(highscore)

#adding/ updating columns
df["result"]=np.where(df['Marks']>=75, "pass", "fail")

#update marks
df.loc[df["Name"]=="John","Marks"]=69
print(df)