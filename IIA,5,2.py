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
                #print(f"Request rejected at time {self.env.now}. Total rejected: {self.total_rejected}")

    def user3(self, k, Q):
        with self.server_pool.request() as req:
            yield req  # Wait for server availability

            # Implement user3 logic here...
           # print(f"User3 with k={k} and Q={Q} handling request at time {self.env.now}")

            # Simulate the processing time
            yield self.env.timeout(1 / self.mu)  # Representing streaming duration as per 1/mu

           # print(f"User3 with k={k} and Q={Q} finished processing at time {self.env.now}")

# Model 2: Data Center Server Tuning
class DataCenter:
    def __init__(self, env, energy_cost_model):
        self.env = env
        self.servers = simpy.Container(env, init=3, capacity=10)  # Initialize servers with a maximum capacity of 10
        self.energy_cost_model = energy_cost_model  # Inkluderer energy_cost_model

    def increase_servers(self):
        yield self.servers.put(1)  # Add one server

    def decrease_servers(self):
        if self.servers.level > 0:
            yield self.servers.get(1)  # Remove one server

    def condition_increase(self):
        # Logg status for bedre innsikt
        print(f"[Time {self.env.now}] Server increased: Current servers = {self.servers.level}, Energy Price = {self.energy_cost_model.elprice}")
        return self.servers.level < 10 and (self.energy_cost_model.elprice == "low" or self.energy_cost_model.elprice == "medium")

    def condition_decrease(self):
        # Logg status for bedre innsikt
        print(f"[Time {self.env.now}] Server decreased: Current servers = {self.servers.level}, Energy Price = {self.energy_cost_model.elprice}")
        return self.servers.level > 2 and (self.energy_cost_model.elprice == "high")

    def up_model(self):
        while True:
            yield self.env.timeout(1)  # Wait for some time
            if self.condition_increase():
                #yield self.energy_cost_model.price_low_event  # wait for low price signal
                yield self.env.process(self.increase_servers())
            else:
                yield self.env.timeout(1)

    def down_model(self):
        while True:
            yield self.env.timeout(1)  # Wait for some time
            if self.condition_decrease():
                #yield self.energy_cost_model.price_high_event  # wait for high price signal
                yield self.env.process(self.decrease_servers())
            else:
                yield self.env.timeout(1)

# Model 3: Energy Cost Model
class EnergyCostModel:
    def __init__(self, env, pmh, expected_times):
        self.env = env
        self.elprice = "low"
        self.pmh = pmh  # Probability of switching from medium to high
        self.expected_times = expected_times  # Expected times for each price level
        self.price_high_event = simpy.Event(env)
        self.price_low_event = simpy.Event(env)

    def wait_until(self, condition):
        while not condition():
            yield self.env.timeout(1)

    def price_change(self):
        while True:
            if self.elprice == "low":
                yield from self.wait_until(lambda: random.expovariate(1/self.expected_times["low"]) < 1)
                self.elprice = "medium"

            elif self.elprice == "medium":
                yield from self.wait_until(lambda: random.expovariate(1/self.expected_times["medium"]) < 1)
                switch_to_high = random.random() < self.pmh
                if switch_to_high:
                    self.elprice = "high"
                    self.price_high_event.succeed()  # trigger high price event
                    self.price_high_event = simpy.Event(self.env)  # reset event
                    yield from self.wait_until(lambda: random.expovariate(1/self.expected_times["high"]) < 1)
                    self.elprice = "medium"
                else:
                    self.elprice = "low"
                    self.price_low_event.succeed()  # trigger low price event
                    self.price_low_event = simpy.Event(self.env)  # reset event

            print(f"[Time {self.env.now}] Energy price changed to {self.elprice}")


def main():
    sim_duration = 10  # Total simulation duration (adjust as needed)
    lambda_ = 60  # Arrival rate (requests per unit of time)
    mu = 1  # Service rate (requests processed per unit of time)
    Qmin = 0.5  # Minimum value for Q

    pmh = 0.5  # Probability of switching from medium to high
    expected_times = {
        "low": 0.1,
        "medium": 1,
        "high": 5
    }  # Expected times for each price level

    env = simpy.Environment()

    # Create instances of the three models
    energy_cost_model = EnergyCostModel(env, pmh, expected_times)
    elastic_dc = ElasticDataCenter(env, lambda_, mu, Qmin, energy_cost_model)
    data_center = DataCenter(env, energy_cost_model)

    # Define the simulation processes
    env.process(elastic_dc.generate_requests())
    env.process(data_center.up_model())
    env.process(data_center.down_model())
    env.process(energy_cost_model.price_change())

    # Run the simulation
    env.run(until=sim_duration)

if __name__ == "__main__":
    main()
