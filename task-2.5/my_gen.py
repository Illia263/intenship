import csv
def gen():    
    with open('task-2.5/dataset.csv', 'r') as f:
        yield from (float(row['total_amount']) *2 for row in csv.DictReader(f))
my_gen = gen()
print(next(my_gen))
print(next(my_gen))
print(next(my_gen))
print(next(my_gen))
print(next(my_gen))