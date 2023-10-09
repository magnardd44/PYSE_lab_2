import simpy
import random

# Parameters and Global variables
lambda_ = 60
mu = 1
sim_duration = 2
n = 5
num_requests = 0
total_rejected = 0

# Functions
def calculate_Q(m, n, k):
    return min(1, m * n / k)

def calculate_MOS(Q):
    q = [0.0, 0.5, 0.6, 0.8, 0.9, 1.0]
    for i in range(1, 6):
        if q[i-1] < Q <= q[i]:
            return i
    return 1

def generate_requests(env, lambda_):
    global num_requests
    while True:
        interarrival_time = random.expovariate(lambda_)
        yield env.timeout(interarrival_time)
        num_requests += 1
        env.process(user3(env, num_requests))

def user3(env, k):
    global total_rejected
    Q = calculate_Q(1, 1, k) 
    if Q > 0.5:
        with server_pool.request() as req:
            yield req
            print(f"User3 with k={k} and Q={Q} handling request at time {env.now}")
            yield env.timeout(1/mu)
            print(f"User3 with k={k} and Q={Q} finished processing at time {env.now}")
    else:
        total_rejected += 1
        print(f"Request rejected at time {env.now}. Total rejected: {total_rejected}")

# Setup and Run simulation
env = simpy.Environment()
server_pool = simpy.Resource(env, capacity=n)
env.process(generate_requests(env, lambda_))
env.run(until=sim_duration)

# Display results
print(f"Total number of generated requests: {num_requests}")
print(f"Total number of rejected requests: {total_rejected}")
