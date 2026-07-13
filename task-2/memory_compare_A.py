import time
import tracemalloc
import csv

file_path = 'task-2/dataset.csv'


start_time = time.perf_counter()
tracemalloc.start()

def with_lst():
    with open(file_path, 'r') as fn:
        reader = list(csv.DictReader(fn))
        return sum([float(row['total_amount']) for row in reader])
lst = with_lst()
print(f"Sum is: {lst:.2f}")

        

_,peak = tracemalloc.get_traced_memory()

peak_1 = peak / 1024 * 2
tracemalloc.stop()
end_time = time.perf_counter()
duration = end_time - start_time
print(f"Current and peak memory usage: {peak_1}, duration: {duration:.2f}")
