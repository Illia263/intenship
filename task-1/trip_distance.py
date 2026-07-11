import pandas as pd

file_path = 'task-1/yellow_tripdata_2026-03.parquet'

df = pd.read_parquet(file_path)
payment_map = { 
    0 : "Flex Fare trip",
    1 : "Credit card",
    2 : "Cash",
    3 : "No charge",
    4 : "Dispute",
    5 : "Unknown",
    6 : "Voided trip"
}
df['payment_type_name'] = df['payment_type'].map(payment_map)
ans = df.groupby(['passenger_count', 'payment_type_name']).agg({'trip_distance' : 'mean'}).round(2)
print(ans)
