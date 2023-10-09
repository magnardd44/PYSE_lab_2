import simpy
import random


USER_ENERGY_USAGE = 200  # energy usage per user k [kWh]
RESOURCE_ENERGY_CAPACITY = 200  # energy capacity per resource [kWh]
RESOURCES_PER_SERVER = 5  # number of resources per server
SERVER_ENERGY_CAPACITY = 1000  # total energy capacity per server [kWh]

N_MAX = 10
N_MIN = 2
M = 5
N = 5
Q_MIN = 0.5
LAMBDA = 60
STREAMING_DURATION = 1
POWER_PER_SERVER = 1000
POWER_PER_RESOURCE = 200
EXPECTED_ENERGY_PER_ACTIVE_USER = 200
LOW_ELECTRICITY_PRICE = 0.1
MEDIUM_ELECTRICITY_PRICE = 1
HIGH_ELECTRICITY_PRICE = 5
TIME_IN_LOW = 1
TIME_IN_MEDIUM = 1
TIME_IN_HIGH = 2


total_rejected = 0

Q = 10

k = 0


def generator(env):
    global k
    while True:
        interval_time = random.expovariate(LAMBDA)

        yield env.timeout(interval_time)

        k += 1

        new_user = User3(env)

        for _ in new_user.lifeCycle():
            pass

        # print(f"Current number of users: {k}")


class User3:
    def __init__(self, env):
        self.env = env

    def calculate_Q(self, m, n, k):
        """
        Calculate the Q factor as per given formula: Q = min(1, m*n/k)
        """
        return min(1, m * n / k)

    def calculate_MOS(self, Q):
        """
        Calculate the MOS score based on the Q factor using the given step function.
        """
        # Threshold values
        q = [0.0, 0.5, 0.6, 0.8, 0.9, 1.0]

        # Define MOS score
        for i in range(1, 6):
            if q[i - 1] < Q <= q[i]:
                return i

        # Default MOS score if Q does not match any condition
        # (not needed if Q is always within the predefined thresholds)
        return 1

    def lifeCycle(self):
        global k
        global total_rejected
        global Q
        global Q_MIN
        global M
        global N
        global LAMBDA

        self.calculate_Q(M, N, k)

        interval_time = random.expovariate(LAMBDA)

        if Q > Q_MIN:
            yield self.env.timeout(interval_time)

            print(k)

            k -= 1

            # Q = self.calculate_Q(M, N, k)

        else:
            k -= 1
            total_rejected += 1


class DataCenter:
    def __init__(self, env):
        self.env = env

    def res(self):
        print("Datacenter")


class ElPriceCalculator:
    def __init__(self, env):
        self.env = env

    def res(self):
        print("ElPrice")


def main():
    global k

    env = simpy.Environment()

    sim_duration = 5  # Total simulation duration (adjust as needed)
    lambda_ = 60  # Arrival rate (requests per unit of time)
    mu = 1  # Service rate (requests processed per unit of time)
    Qmin = 0.5  # Minimum value for Q
    durations = {"low": 1, "medium": 1, "high": 2}  # in hours  # in hours  # in hours
    prices = {
        "low": 0.1,  # in NOK/kWh
        "medium": 1,  # in NOK/kWh
        "high": 5,  # in NOK/kWh
    }

    env.process(generator(env))

    # Run the simulation
    env.run(until=sim_duration)


if __name__ == "__main__":
    main()
