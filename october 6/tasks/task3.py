import pandas as pd
import logging

logging.basicConfig(filename='task3.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
data = {
    'product': ['Laptop', 'Mouse', 'Keyboard'],
    'price': [70000, 500, 1200],
    'quantity': [2, 5, 3]
}
df=pd.DataFrame(data)

try:
    df.to_csv("sales.csv",index=False)
except FileExistsError as e:
    print(e)
    logging.warning("sales.csv already exists")
logging.info("Data saved csv created")
try:
    a=pd.read_csv("sales.csv")
    logging.info("read csv successfully")
except FileNotFoundError as e:
    print(e)
    logging.error("File not found")
try:
    a["total_sales"]=a["price"]*a["quantity"]
except ValueError as e:
    print(e)
    logging.error("Value error needs numeric values")
for index,row in a.iterrows():
    logging.info(f"{row['product']}--{row['total_sales']}")