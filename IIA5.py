import simpy
import random


# Model 1: Elastic Data Center
class ElasticDataCenter:
    def __init__(self, env, lambda_, mu, Qmin, energy_cost_model):
        self.env = env
        self.n = 5  # Number of servers
        self.server_pool = simpy.Resource(env, capacity=self.n)
        self.lambda_ = lambda_
        self.mu = mu
        self.Qmin = Qmin
        self.total_rejected = 0
        self.energy_cost_model = energy_cost_model

    def generate_requests(self):
        k = 0  # Initialize k
        while True:
            # Generate an inter-arrival time from an exponential distribution
            interarrival_time = random.expovariate(self.lambda_)

            # Yield an event for the next request arrival
            yield self.env.timeout(interarrival_time)

            # Calculate Q based on the described logic
            Q = min(1, self.server_pool.count / k) if k > 0 else 1

            # Check if Q is greater than Qmin
            if Q > self.Qmin:
                k += 1
                self.env.process(self.user3(k, Q))
            else:
                k -= 1
                self.total_rejected += 1
                print(
                    f"Request rejected at time {self.env.now}. Total rejected: {self.total_rejected}"
                )

    def user3(self, k, Q):
        with self.server_pool.request() as req:
            yield req  # Wait for server availability

            # Implement user3 logic here...
            print(f"User3 with k={k} and Q={Q} handling request at time {self.env.now}")

            # Simulate the processing time
            yield self.env.timeout(
                1 / self.mu
            )  # Representing streaming duration as per 1/mu

            print(
                f"User3 with k={k} and Q={Q} finished processing at time {self.env.now}"
            )


# Model 2: Data Center Server Tuning
class DataCenter:
    def __init__(self, env):
        self.env = env
        self.servers = simpy.Container(
            env, init=0, capacity=10
        )  # Initialize servers with a maximum capacity of 10

    def increase_servers(self):
        self.servers.put(1)  # Add one server
        print(f"Server increased: {self.env.now}")

    def decrease_servers(self):
        if self.servers.level > 0:
            self.servers.get(1)  # Remove one server
            print(f"Server decreased: {self.env.now}")

    def condition_increase(self):
        # Add your condition for increasing servers here
        return self.servers.level < 5

    def condition_decrease(self):
        # Add your condition for decreasing servers here
        return self.servers.level > 2

    def up_model(self):
        while True:
            yield self.env.timeout(1)  # Wait for some time

            if self.condition_increase():
                self.increase_servers()
            else:
                yield self.env.timeout(
                    1
                )  # Wait until the condition is met for increasing

    def down_model(self):
        while True:
            yield self.env.timeout(1)  # Wait for some time

            if self.condition_decrease():
                self.decrease_servers()
            else:
                yield self.env.timeout(
                    1
                )  # Wait until the condition is met for decreasing


# Model 3: Energy Cost Model
class EnergyCostModel:
    def __init__(self, env, pmh, expected_times):
        self.env = env
        self.elprice = "low"
        self.pmh = pmh  # Probability of switching from medium to high
        self.expected_times = expected_times  # Expected times for each price level

    def wait_until(self, condition):
        while not condition():
            yield self.env.timeout(1)

    def price_change(self):
        while True:
            if self.elprice == "low":
                yield from self.wait_until(
                    lambda: random.expovariate(1 / self.expected_times["low"]) < 1
                )
                self.elprice = "medium"

            elif self.elprice == "medium":
                yield from self.wait_until(
                    lambda: random.expovariate(1 / self.expected_times["medium"]) < 1
                )
                switch_to_high = random.random() < self.pmh
                if switch_to_high:
                    self.elprice = "high"
                    yield from self.wait_until(
                        lambda: random.expovariate(1 / self.expected_times["high"]) < 1
                    )
                    self.elprice = "medium"
                else:
                    self.elprice = "low"


def main():
    sim_duration = 10  # Total simulation duration (adjust as needed)
    lambda_ = 60  # Arrival rate (requests per unit of time)
    mu = 1  # Service rate (requests processed per unit of time)
    Qmin = 0.5  # Minimum value for Q

    pmh = 0.2  # Probability of switching from medium to high
    expected_times = {
        "low": 4,
        "medium": 3,
        "high": 2,
    }  # Expected times for each price level

    env = simpy.Environment()

    # Create instances of the three models
    energy_cost_model = EnergyCostModel(env, pmh, expected_times)
    elastic_dc = ElasticDataCenter(env, lambda_, mu, Qmin, energy_cost_model)
    data_center = DataCenter(env)

    # Define the simulation processes
    env.process(elastic_dc.generate_requests())
    env.process(data_center.up_model())
    env.process(data_center.down_model())
    env.process(energy_cost_model.price_change())

    # Run the simulation
    env.run(until=sim_duration)


if __name__ == "__main__":
    main()
