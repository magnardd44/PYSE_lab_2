import simpy
import random


def calculate_Q(m, n, k):
    """
    Calculate the Q factor as per given formula: Q = min(1, m*n/k)

    Parameters:
    - m, n, k: parameters related to bandwidth.

    Returns:
    float: Q factor
    """
    return min(1, m * n / k)


# Implement user and combine it with the generator.

sim_duration = 1  # simulation duration
lambda_ = 60  # replace with the correct value

env = simpy.Environment()
num_requests = 0  # Initialize a counter for the number of generated requests
n = 5  # number of servers
server_pool = simpy.Resource(env, capacity=n)  # Initialize server pool
k = 0
Qmin = 0.5


# Function to generate requests and user3
def generate_requests(env, lambda_, user):
    global num_requests
    while True:
        # Generate an inter-arrival time from an exponential distribution
        interarrival_time = random.expovariate(lambda_)

        # Yield an event for the next request arrival
        yield env.timeout(interarrival_time)

        # Increment the request counter
        num_requests += 1
        print(f"Request #{num_requests} generated at time {env.now}")
        env.process(user(env, num_requests))


def user3(env, request_id):
    global k

    print(f"User3 handling request {request_id} at time {env.now}")
    with server_pool.request() as req:
        yield req  # Wait for server availability

        print(f"Request {request_id} being processed at time {env.now}")

        k = k + 1

        Q = calculate_Q(5, 5, k)

        try:
            if Q <= Qmin:
                k = k - 1
                raise simpy.Interrupt("Q <= Qmin")

            else:
                k = k - 1
                Q = min(5, 5, k)

                if Q < 1:
                    raise simpy.Interrupt("Q < 1")
        except simpy.Interrupt as interrupt:
            print(f"Interrupt occured: {interrupt}")

        print(f"Number K:  {k}")

        print(f"Request {request_id} finished processing at time {env.now}")


# Start the request generation process
process = env.process(generate_requests(env, lambda_, user3))
env.run(until=sim_duration)
print(f"Total number of generated requests: {num_requests}")
