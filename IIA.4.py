import simpy
import random

# Implement user and combine it with the generator.

sim_duration = 2  # simulation duration
lambda_ = 1  # replace with the correct value
mu = 1  # replace with the correct value

env = simpy.Environment()
num_requests = 0  # Initialize a counter for the number of generated requests
n = 5  # number of servers
server_pool = simpy.Resource(env, capacity=n)  # Initialize server pool


# Function to generate requests and user3
def generate_requests(env, lambda_, user3):
    global num_requests
    while True:
        # Generate an inter-arrival time from an exponential distribution
        interarrival_time = random.expovariate(lambda_)
        
        # Yield an event for the next request arrival
        yield env.timeout(interarrival_time)
        
        # Increment the request counter
        num_requests += 1
        print(f"Request #{num_requests} generated at time {env.now}")
        env.process(user3(env, num_requests))


def user3(env, request_id):
    print(f"User3 handling request {request_id} at time {env.now}")
    with server_pool.request() as req:
        yield req  # Wait for server availability

        print(f"Request {request_id} being processed at time {env.now}")

        # Implement your user logic and server interactions here.
        yield env.timeout(1/mu)  # Representing streaming duration as per 1/mu
        
        print(f"Request {request_id} finished processing at time {env.now}")


# Start the request generation process
env.process(generate_requests(env, lambda_, user3))
env.run(until=sim_duration)
print(f"Total number of generated requests: {num_requests}")

