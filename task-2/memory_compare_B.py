import pandas as pd
import time
import csv
import tracemalloc
file_path = 'task-2/dataset.csv'

start_time = time.perf_counter()
tracemalloc.start()

def with_gen():
    with open(file_path , 'r') as fn:
        return sum(float(row['total_amount']) for row in csv.DictReader(fn))
total_sum = with_gen()    
print(f'Total sum is: {total_sum:.2f}')

peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
end_time = time.perf_counter()
duration = end_time - start_time
print(f'Current and peak memorty usage: {peak}, duration: {duration:.2f}')




def with_lst():
    with open('dataset.csv', 'r') as fn:
        reader = list(csv.DictReader(fn))
        return sum([float(row['total_amount']) for row in reader])