import simpy
import numpy as np

env = simpy.Environment()
SIM_TIME = 60 * 24

runway = simpy.Resource(env, capacity=1)


def flying_time():
    return np.random.exponential(60)


def inter_arrival_time():
    return np.random.exponential(30)


def airplane_generator(env):
    i = 1
    while True:
        yield env.timeout(inter_arrival_time())
        env.process(airplane(env, i))
        i += 1


def airplane(env, id):
    print(f"Airplane {id} in air")
    take_off_time = env.now
    yield env.timeout(flying_time())
    time_in_air = env.now - take_off_time

    start_landing = env.now
    print(f"Airplane {id} requests runway for landing")
    req = runway.request()
    yield req
    runway_wait = env.now - start_landing
    print(f"Airplane {id} waited for runway for {runway_wait} minutes")
    yield env.timeout(30)
    runway.release(req)

    print(f"Airplane {id} landed after {time_in_air + runway_wait+ 30} minutes")


sim = env.process(airplane_generator(env))

env.run(until=SIM_TIME)
