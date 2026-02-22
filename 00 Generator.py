import simpy
import random
import csv
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

x = sp.symbols('x')

f = x**2 + 2*x + 1
f_numeric = sp.lambdify(x, f)



results = []

START_HOUR = 9
MINUTES_PER_UNIT = 1

def time_to_str(t):
    """Convert simulation minutes → nice hh:mm string"""
    minutes_total = START_HOUR * 60 + t * MINUTES_PER_UNIT
    h = int(minutes_total // 60) % 24
    m = int(minutes_total % 60)
    return f"{h:02d}:{m:02d}"

def main():
    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=2)
    env.process(customer_generator(env, counter))
    env.run(until=450)
    print("Simulation finished")

    write_log_to_csv()

def supermarket_shopping(env, name, counter):
    enter_time = time_to_str(env.now)
    print(f"{name} enters the supermarket at {enter_time}")
    yield env.timeout(random.randint(1, 3))
    shopping_time = time_to_str(env.now)
    print(f"{name} finishes shopping at {shopping_time}")
    yield env.timeout(random.randint(5, 30))
    start_queue = time_to_str(env.now)
    print(f"{name} stands in queue at {start_queue}")
    with counter.request() as request:
        yield request
        checkout_start = time_to_str(env.now)
        yield env.timeout(random.randint(1, 5))
        paying_time = time_to_str(env.now)
        print(f"{name} pays at {paying_time}")
        yield env.timeout(random.randint(1, 2))
        packing_time = time_to_str(env.now)
        print(f"{name} packs items at {packing_time}")
        yield env.timeout(random.randint(1, 3))
        leave_time = time_to_str(env.now)
        print(f"{name} leaves at {leave_time}")
        yield env.timeout(.5)

    results.append([
        name,
        enter_time,
        shopping_time,
        start_queue,
        checkout_start,
        paying_time,
        packing_time,
        leave_time
    ])

def customer_generator(env, counter):
    customer_id = 0
    while True:
        customer_id += 1
        env.process(supermarket_shopping(env, f"Customer {customer_id}", counter))

        arrival_time = random.randint(1, 5)
        yield env.timeout(arrival_time)

def write_log_to_csv():
    with open("supermarket_simulation.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["customer","enter_time","shopping_time","start_queue","checkout_start","paying_time","packing_time","leave_time"])
        writer.writerows(results)

print("CSV file created!")


if __name__ == "__main__":
    main()
