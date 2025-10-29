import pandas as pd
from datetime import datetime

def run_pipeline():
    df=pd.read_csv("Sales.csv")
    df['Total']=df['Price']*df['Quantity']
    df.to_csv("TotalSales.csv", index=False)
    print(f"pipeline completed at {datetime.now()}")


if __name__ == "__main__":
    run_pipeline()