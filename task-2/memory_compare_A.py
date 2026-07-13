import time
import tracemalloc
import csv

file_path = 'task-2/dataset.csv'


start_time = time.perf_counter()
tracemalloc.start()

with open(file_path, 'r') as f:
    reader = list(csv.DictReader(f))
    # total_sum = 0
    for row in reader:
        total_sum = sum(float(row['total_amount']))
        
        
    print(f'Total sum is: {total_sum:.2f}')
peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
end_time = time.perf_counter()
duration = end_time - start_time
print(f"Current and peak memory usage: {peak}, duration: {duration:.2f}")