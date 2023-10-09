import simpy
import random

sim_duration = 2  # Simulation duration (adjust as needed)
lambda_ = 60  # Arrival rate (requests per unit of time)
mu = 1  # Service rate (requests processed per unit of time)
Qmin = 0.5  # Minimum value for Q
total_rejected = 0  # Initialize a counter for rejected requests

env = simpy.Environment()
n = 5  # Number of servers
server_pool = simpy.Resource(env, capacity=n)  # Initialize server pool


def generate_requests(env, lambda_, user3):
    global total_rejected
    k = 0  # Initialize k
    while True:
        # Generate an inter-arrival time from an exponential distribution
        interarrival_time = random.expovariate(lambda_)

        # Yield an event for the next request arrival
        yield env.timeout(interarrival_time)

        # Calculate Q based on the described logic
        Q = min(1, server_pool.count / k) if k > 0 else 1

        # Check if Q is greater than Qmin
        if Q > Qmin:
            k += 1
            env.process(user3(env, k, Q))
        else:
            k = max(0, k - 1)
            total_rejected += 1
            print(
                f"Request rejected at time {env.now}. Total rejected: {total_rejected}"
            )


def user3(env, k, Q):
    with server_pool.request() as req:
        yield req  # Wait for server availability

        # Implement user3 logic here...
        print(f"User3 with k={k} and Q={Q} handling request at time {env.now}")

        # Simulate the processing time
        yield env.timeout(1)  # Representing streaming duration as per 1/mu

        print(f"User3 with k={k} and Q={Q} finished processing at time {env.now}")


# Start the request generation process
env.process(generate_requests(env, lambda_, user3))
env.run(until=sim_duration)

print(
    f"Total number of generated requests: {server_pool.capacity * (sim_duration / mu)}"
)
print(f"Total number of rejected requests: {total_rejected}")
