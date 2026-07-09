import pandas as pd
file_path = 'task-1/yellow_tripdata_2026-03.parquet'

df = pd.read_parquet(file_path)

df['travel_time'] = df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
df['travel_time_in_hours'] = df['travel_time'].dt.total_seconds()/3600
df['avg_speed'] = df['trip_distance'] / df['travel_time_in_hours']
ans = df[['avg_speed']]
print(ans)