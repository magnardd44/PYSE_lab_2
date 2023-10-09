import simpy
import numpy as np

env = simpy.Environment()


def flying_time():
    return np.random.exponential(60)


def airplane(env):
    print("Airplane in air")
    take_off_time = env.now
    yield env.timeout(flying_time())
    time_in_air = env.now - take_off_time
    print(f"Airplane landed after {time_in_air} minutes")


sim = env.process(airplane(env))

env.run()
