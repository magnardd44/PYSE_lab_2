import simpy
import random


# Define the arrival rate (intensity) lambda
lambda_ = 60  # Adjust this to your desired rate
sim_duration = 2 # Adjust this to your desired simulation duration

# Create a SimPy environment
env = simpy.Environment()

# Initialize a counter for the number of generated requests
num_requests = 0

# Function to generate requests
def generate_requests(env, lambda_):
    global num_requests
    while True:
        # Generate an inter-arrival time from an exponential distribution
        interarrival_time = random.expovariate(lambda_)
        
        # Yield an event for the next request arrival
        yield env.timeout(interarrival_time)
        
        # Increment the request counter
        num_requests += 1
        print(f"Request #{num_requests} generated at time {env.now}")

# Start the request generation process
env.process(generate_requests(env, lambda_))

# Run the simulation for a certain duration (or until a certain condition)
env.run(until=sim_duration)

# Print the total number of generated requests
print(f"Total number of generated requests: {num_requests}")

