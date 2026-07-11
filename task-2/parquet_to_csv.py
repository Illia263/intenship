import pandas as pd

df = pd.read_parquet('task-2/yellow_tripdata_2026-03.parquet')
df.to_csv('dataset.csv', index=False)
