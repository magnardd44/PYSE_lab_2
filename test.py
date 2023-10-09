import simpy
import random

# Parametere fra tabell 2
params = {
    'lambda_': 60,  # request rate
    'mu': 1,  # streaming duration
    'Nmax': 10,
    'Nmin': 2,
    'm': 5,  # slices per server
    'n_servers': 5,  # dette antallet må kanskje justeres
    #... andre parametere ...
}

# Global variables
num_requests = 0
num_served_requests = 0

# Request generator
def generate_requests(env, lambda_):
    global num_requests
    while True:
        interarrival_time = random.expovariate(lambda_)
        yield env.timeout(interarrival_time)
        num_requests += 1
        print(f"Request #{num_requests} generated at time {env.now}")
        env.process(user3(env))

# User function
def user3(env):
    global num_served_requests
    print(f"User3 starts streaming at time {env.now}")
    streaming_duration = random.expovariate(params['mu'])
    yield env.timeout(streaming_duration)
    num_served_requests += 1
    print(f"User3 finishes streaming at time {env.now}")

# Create SimPy environment
env = simpy.Environment()

# Add resources (servers)
servers = simpy.Resource(env, capacity=params['n_servers'])

# Start processes
env.process(generate_requests(env, params['lambda_']))

# Run the simulation
sim_duration = 2  # her setter du ønsket simuleringsvarighet
env.run(until=sim_duration)

# Output
print(f"Total number of generated requests: {num_requests}")
print(f"Total number of served requests: {num_served_requests}")
