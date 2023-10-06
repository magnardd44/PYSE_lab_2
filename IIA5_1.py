import simpy
import random
import matplotlib.pyplot as plt

class ElasticDataCenter:
    def __init__(self, env, lambda_, mu, Qmin, energy_cost_model):
        self.env = env
        self.n = 5  
        self.server_pool = simpy.Resource(env, capacity=self.n)
        self.lambda_ = lambda_
        self.mu = mu
        self.Qmin = Qmin
        self.total_rejected = 0
        self.energy_cost_model = energy_cost_model

        self.server_usage = []  # Added to collect usage stats

    def generate_requests(self):
        k = 0  
        while True:
            interarrival_time = random.expovariate(self.lambda_)
            yield self.env.timeout(interarrival_time)
            print(f"Request arrived at time {self.env.now}.")
            Q = min(1, self.server_pool.count / k) if k > 0 else 1
            if Q > self.Qmin:
                k += 1
                self.env.process(self.user3(k, Q))
            else:
                k -= 1
                self.total_rejected += 1
                print(f"Request rejected at time {self.env.now}. Total rejected: {self.total_rejected}")

    def user3(self, k, Q):
        with self.server_pool.request() as req:
            yield req  
            print(f"User3 with k={k} and Q={Q} handling request at time {self.env.now}. Server count: {self.server_pool.count}.")
            yield self.env.timeout(1 / self.mu)
            print(f"User3 with k={k} and Q={Q} finished processing at time {self.env.now}.")

            self.server_usage.append((self.env.now, self.server_pool.count))  # Added to collect usage stats

class DataCenter:
    def __init__(self, env, energy_cost_model, Nmin):
        self.env = env
        self.Nmin = Nmin
        self.servers = simpy.Container(env, init=0, capacity=10)
        self.energy_cost_model = energy_cost_model


    def increase_servers(self):
        self.servers.put(1)  
        print(f"Server increased at time {self.env.now}. Total servers: {self.servers.level}.")

    def decrease_servers(self):
        if self.servers.level > 0:
            self.servers.get(1)
            print(f"Server decreased at time {self.env.now}. Total servers: {self.servers.level}.")

    def condition_increase(self):
        print(f"Checking increase condition at time {self.env.now}. Server count: {self.servers.level}. Price: {self.energy_cost_model.elprice}.")
        return self.servers.level < 5 and self.energy_cost_model.elprice == "low"

    def condition_decrease(self):
        print(f"Checking decrease condition at time {self.env.now}. Server count: {self.servers.level}. Price: {self.energy_cost_model.elprice}.")
        return self.servers.level > self.Nmin and self.energy_cost_model.elprice == "high"

    def up_model(self):
        while True:
            yield self.env.timeout(1)
            if self.condition_increase():
                self.increase_servers()

    def down_model(self):
        while True:
            yield self.env.timeout(1)
            if self.condition_decrease():
                self.decrease_servers()
   
class EnergyCostModel:
    def __init__(self, env, pmh, expected_times):
        self.env = env
        self.elprice = "low"
        self.pmh = pmh
        self.expected_times = expected_times

        self.price_changes = []  # Added to collect price change stats

    def wait_until(self, condition):
        while not condition():
            yield self.env.timeout(1)

    def price_change(self):
        while True:
            print(f"Price is {self.elprice} at time {self.env.now}.")
            if self.elprice == "low":
                yield from self.wait_until(lambda: random.expovariate(1/self.expected_times["low"]) < 1)
                self.elprice = "medium"
            elif self.elprice == "medium":
                yield from self.wait_until(lambda: random.expovariate(1/self.expected_times["medium"]) < 1)
                if random.random() < self.pmh:
                    self.elprice = "high"
                else:
                    self.elprice = "low"
            elif self.elprice == "high":
                yield from self.wait_until(lambda: random.expovariate(1/self.expected_times["high"]) < 1)
                self.elprice = "medium"
            self.price_changes.append((self.env.now, self.elprice))  # Added to collect price change stats

def plot_results(elastic_dc, energy_cost_model):
    fig, ax1 = plt.subplots()

    # Plotting server usage
    times, server_counts = zip(*elastic_dc.server_usage)
    ax1.plot(times, server_counts, 'b-')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Server Count', color='b')
    ax1.tick_params(axis='y', labelcolor='b')

    ax2 = ax1.twinx()  

    # Plotting electricity price changes
    times, prices = zip(*energy_cost_model.price_changes)
    ax2.plot(times, [0 if p=="low" else 1 if p=="medium" else 2 for p in prices], 'r-')
    ax2.set_ylabel('Electricity Price Level', color='r') 
    ax2.tick_params(axis='y', labelcolor='r')
    
    fig.tight_layout()  
    plt.show()

def main():
    sim_duration = 100  
    lambda_ = 60  
    mu = 1  
    Qmin = 0.4  
    
    pmh = 0.5  
    expected_times = {
        "low": 4,
        "medium": 3,
        "high": 2
    }  

    Nmin = 2

    env = simpy.Environment()
    energy_cost_model = EnergyCostModel(env, pmh, expected_times)
    elastic_dc = ElasticDataCenter(env, lambda_, mu, Qmin, energy_cost_model)
    data_center = DataCenter(env, energy_cost_model, Nmin)

    env.process(elastic_dc.generate_requests())
    env.process(data_center.up_model())
    env.process(data_center.down_model())
    env.process(energy_cost_model.price_change())
    env.run(until=sim_duration)

    # return the instances so they can be used for plotting
    return elastic_dc, energy_cost_model


if __name__ == "__main__":
   elastic_dc, energy_cost_model = main()
   plot_results(elastic_dc, energy_cost_model)
