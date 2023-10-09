import simpy
import random

sim_duration = 10  # Simulation duration (adjust as needed)
lambda_ = 60  # Arrival rate (requests per unit of time)
mu = 1  # Service rate (requests processed per unit of time)
Qmin = 0.5  # Minimum value for Q
total_rejected = 0  # Initialize a counter for rejected requests

n = 5  # Number of servers
m = 5  # Resources per server
env = simpy.Environment()
server_pool = simpy.Resource(env, capacity=n * m)  # Initialize server pool


def generate_requests(env, lambda_, user3):
    global total_rejected
    k = 0  # Initialize k
    while True:
        k += 1
        print("Run")

        with server_pool.request() as req:
            yield req  # Request a server

            interarrival_time = random.expovariate(lambda_)

            # Yield an event for the next request arrival
            yield env.timeout(interarrival_time)

            print(k)
            print(server_pool.count)

            # Calculate Q based on the described logic
            Q = min(1, server_pool.count / k)

            print(Q)

            # Check if Q is greater than Qmin
            if Q > Qmin:
                env.process(user3(env, k, Q))
                server_pool.release(
                    req
                )  # Release the server, increasing server_pool.count
                k -= 1

            else:
                k -= 1
                total_rejected += 1
                print(
                    f"Request rejected at time {env.now}. Total rejected: {total_rejected}"
                )


def user3(env, k, Q):
    # Implement user3 logic here...
    print(f"User3 with k={k} and Q={Q} handling request at time {env.now}")

    # Simulate the processing time
    yield env.timeout(1)  # Representing streaming duration

    print(f"User3 with k={k} and Q={Q} finished processing at time {env.now}")


# Start the request generation process
env.process(generate_requests(env, lambda_, user3))
env.run(until=sim_duration)

print(f"Total number of generated requests: {server_pool.capacity * sim_duration}")
print(f"Total number of rejected requests: {total_rejected}")
