import simpy
import random


# Define the arrival rate (intensity) lambda
lambda_ = 60  # Adjust as needed (requests per unit of time)
sim_duration = 2 #simulation duration (adjust as needed) 

# Create a SimPy environment
env = simpy.Environment()

# Initialize a counter for the number of generated requests
user_requests = 0

# Function to generate requests
def generate_requests(env, lambda_):
    global user_requests
    while True:
        # Generate an inter-arrival time from an exponential distribution
        interarrival_time = random.expovariate(lambda_)
        
        # Yield an event for the next request arrival
        yield env.timeout(interarrival_time)
        
        # Increment the request counter
        user_requests += 1
        print(f"Request #{user_requests} generated at time {env.now}")

# Start the request generation process
env.process(generate_requests(env, lambda_))

# Run the simulation for a certain duration (or until a certain condition)
env.run(until=sim_duration)

# Print the total number of generated requests
print(f"Total number of generated requests: {user_requests}")

