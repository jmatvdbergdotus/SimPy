import simpy
import random
import csv
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from itertools import product

START_HOUR: int = 9 # Simulation starts at 9:00 AM
END_HOUR: int = 18  # Simulation ends at 6:00 PM (9 hours later)
MINUTES_PER_UNIT: int = 1
MINUTES_SIMULATION: int = (END_HOUR - START_HOUR) * 60 // MINUTES_PER_UNIT
LOGGING_ENABLED: bool = False # Set to True to enable detailed logging of customer activities

def time_to_str(time: float) -> str:
    """Convert simulation minutes → nice hh:mm string"""
    minutes_total: int = START_HOUR * 60 + time * MINUTES_PER_UNIT
    hours: int = int(minutes_total // 60) % 24
    minutes: int = int(minutes_total % 60)
    return f"{hours:02d}:{minutes:02d}"

def main():
    shopping_items_time: list[int] = [20, 30]  # Different shopping times to test
    packing_items_time: list[int]  = [3, 15]   # Different packing times to test
    capacity: list[int]            = [1, 2, 3] # Number of checkout counters available

    for sit,pit,cap in product(shopping_items_time, packing_items_time, capacity):
        results = []
        env: simpy.Environment = simpy.Environment()
        counter: simpy.Resource = simpy.Resource(env, capacity=cap)
        self_counter: simpy.Resource = simpy.Resource(env, capacity=cap*2) 
        env.process(customer_generator(env, counter, self_counter, sit, pit, results))
        env.run(until=MINUTES_SIMULATION)
        print("Simulation finished for shopping_items_time =", 
              sit, "and packing_items_time =", pit, "and capacity =", cap)

        write_log_to_csv(f"supermarket_simulation_{sit}_{pit}_{cap}.csv", results)

def print_log(string: str) -> None:
    if LOGGING_ENABLED:
        print(string)

def r_int(max_value: int) -> int:
    return random.randint(1, max_value)

def activity(env: simpy.Environment, customer_name: str, activity_name: str, duration=0) -> str:
    if duration == 0: # Instantaneous activity (e.g., entering, leaving)
        print_log(f"{customer_name} doing {activity_name} at {time_to_str(env.now)}")
        return time_to_str(env.now)
    else:
        start_time = time_to_str(env.now)
        print_log(f"{customer_name} doing {activity_name} starts at {start_time}")
        yield env.timeout(duration)
        end_time = time_to_str(env.now)
        print_log(f"{customer_name} doing {activity_name} ends at {end_time}")
        return end_time

def supermarket_shopping(env: simpy.Environment, name: str, counter, self_counter, 
                         shopping_items_time: int, packing_items_time: int, results) -> None:
    enter_time = yield env.process(activity(env, name, "entering"))
    shopping_time = yield env.process(activity(env, name, "shopping", r_int(shopping_items_time)))
    start_queue = yield env.process(activity(env, name, "queueing"))

    checkout_choice_regular = (r_int(2) == 1) # 50% chance to choose regular checkout, 50% chance to choose self-checkout
    if checkout_choice_regular: 
        with counter.request() as request:
            yield request

            checkout_start = yield env.process(activity(env, name, "checkout"))
            paying_time = yield env.process(activity(env, name, "paying", r_int(5)))
            packing_time = yield env.process(activity(env, name, "packing", r_int(packing_items_time)))
            leave_time = yield env.process(activity(env, name, "leaving"))
            
    else:
        with self_counter.request() as request:
            yield request

            checkout_start = yield env.process(activity(env, name, "self-checkout"))
            paying_time = yield env.process(activity(env, name, "paying", r_int(5)))
            packing_time = yield env.process(activity(env, name, "packing", r_int(packing_items_time)))
            leave_time = yield env.process(activity(env, name, "leaving"))

    yield env.timeout(0.5)

    results.append([name, enter_time, shopping_time, start_queue, checkout_start,
            paying_time, packing_time, leave_time, checkout_choice_regular])

def customer_generator(env: simpy.Environment, counter, self_counter, 
                       shopping_items_time: int, packing_items_time: int, results) -> None:
    customer_id: int = 0
    while True:
        customer_id += 1
        env.process(supermarket_shopping(env, f"Customer {customer_id}", counter, self_counter, 
                                                  shopping_items_time, packing_items_time, results))
        arrival_time = r_int(5)
        yield env.timeout(arrival_time)

def write_log_to_csv(filename: str, results) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["customer","enter_time","shopping_time","start_queue",
                         "checkout_start","paying_time","packing_time",
                         "leave_time","checkout_choice_regular"])
        writer.writerows(results)
    print("CSV file created named", filename)


if __name__ == "__main__":
    main()
