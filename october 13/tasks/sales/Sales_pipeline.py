import pandas as pd
from datetime import datetime

df0=pd.read_csv("Product1.csv")
df1=pd.read_csv("Customer1.csv")
df2=pd.read_csv("Order1.csv")

df3=pd.merge(df1,df2, on='CustomerID', how='inner')
df4=pd.merge(df0,df3,on='ProductID', how='inner')

df4['TotalAmount']=df4['Price']*df4['Quantity']
df4['OrderDate'] = pd.to_datetime(df4['OrderDate']) # Convert to datetime first
df4['OrderMonth'] = df4['OrderDate'].dt.month

df5=df4[df4['Quantity']>2]
print(df5['Quantity'])

df6 = df5[(df5['Country'] == "UAE") | (df5['Country'] == "India")]
print(df6['Country'])

revenue_per_category = df4.groupby('Category')['TotalAmount'].agg('sum').reset_index()
revenue_per_segment = df4.groupby('Segment')['TotalAmount'].agg('sum').reset_index()

print("Total Revenue per Category:")
print(revenue_per_category)
print("\nTotal Revenue per Customer Segment:")
print(revenue_per_segment)

customer_total_revenue = df4.groupby(['CustomerID', 'Name', 'Country', 'Segment'])['TotalAmount'].agg('sum').reset_index()
sorted_customers_by_revenue = customer_total_revenue.sort_values(by='TotalAmount', ascending=False)

# Display the sorted customers
print("Customers Sorted by Total Revenue (Highest to Lowest):")
print(sorted_customers_by_revenue)

df6.to_csv("processed_orders.csv", index=False)

revenue_per_category.to_csv("category_summary.csv", index=False)

revenue_per_segment.to_csv("segment_summary.csv", index=False)


print(f"Pipeline finished at {datetime.now()}")
