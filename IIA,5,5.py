import simpy
import random

# Model 1: Elastic Data Center
class ElasticDataCenter:
    USER_ENERGY_USAGE = 200  # energy usage per user k [kWh]
    RESOURCE_ENERGY_CAPACITY = 200  # energy capacity per resource [kWh]
    RESOURCES_PER_SERVER = 5  # number of resources per server
    SERVER_ENERGY_CAPACITY = 1000  # total energy capacity per server [kWh]
    
    def __init__(self, env, n, lambda_, mu, Qmin, energy_cost_model):
        self.env = env
        self.n = n  # Number of servers
        self.k = 0  # The user id (does not care if a user finishes his task or not)
        self.active_users = 0  # The current number of active users
        self.m = self.n* ElasticDataCenter.RESOURCES_PER_SERVER  # The current number of available resources
        self.lambda_ = lambda_
        self.mu = mu
        self.Qmin = Qmin
        self.total_rejected = 0
        self.energy_cost_model = energy_cost_model
        self.signal_up = simpy.Event(env)
        self.signal_down = simpy.Event(env)
        LOW_ELECTRICITY_PRICE = 0.1
        MEDIUM_ELECTRICITY_PRICE = 1
        HIGH_ELECTRICITY_PRICE = 5
        TIME_IN_LOW = 1
        TIME_IN_MEDIUM = 1
        TIME_IN_HIGH = 2

    def generate_requests(self):
        k = 0  # Initialize k
        while True:
            # Generate an inter-arrival time from an exponential distribution
            interarrival_time = random.expovariate(self.lambda_)

            # Yield an event for the next request arrival
            yield self.env.timeout(interarrival_time)

            # Calculate Q based on the described logic - fair share
            Q = min(1, self.m / self.k) if self.k > 0 else 1

             # Log the values
             # print(
             #     f"Time: {self.env.now:.2f}, k: {k}, Server Pool Count: {self.m}, Q: {Q}"
             # )
            
            potential_users_per_server = (self.k + 1) / self.n if self.n > 0 else float('inf')

            # Check if Q is greater than Qmin
            if Q > self.Qmin and potential_users_per_server <= 4.5:
                    if self.m > 0:
                        k += 1
                        self.k = k 
                        #self.m -= 1 # Reduce the number of available resources
                        #self.active_users += 1
                        self.signal_up.succeed()  
                        self.signal_up = simpy.Event(self.env)
                        self.env.process(self.user3(k, Q))
                    else:
                        self.total_rejected += 1
            else:
                self.total_rejected += 1
                # Adding signaling mechanism here
                self.signal_down.succeed()  # Send signal_down
                self.signal_down = simpy.Event(self.env)  # Reset event


    def monitor_users(self):
        while True:
            print(f"[Time {self.env.now}] Active users (k): {self.k}")
            yield self.env.timeout(1)
            

    def print_final_rejects(self):
        print(f"Total rejected requests at end of simulation: {self.total_rejected}")

    def user3(self, k, Q):
        # Check if resource is available
        while self.m <= 0:
            # Wait for some time or for a signal that resource is available
            yield self.env.timeout(1) or self.signal_up

        # Resource is available
        self.m -= 1  # Reduce the number of available resources
        self.k += 1
        print(f"User3 with k={k} and Q={Q} handling request at time {self.env.now}")

        # Simulate the processing time
        yield self.env.timeout(1 / self.mu)  # Representing streaming duration as per 1/mu

        print(f"User3 with k={k} and Q={Q} finished processing at time {self.env.now}")
        print(f"active users={self.k} Server Pool Count: {self.m}, Q: {Q}")

        # Release the resource
        self.m += 1  # Increase the number of available resources
        self.k -= 1  # Decrease the number of active users

        # Signal that a resource has been released (if any process is waiting for this)
        self.signal_up.succeed()  
        self.signal_up = simpy.Event(self.env)


# Model 2: Data Center Server Tuning
class DataCenter:
    def __init__(self, env, energy_cost_model, elastic_data_center):
        self.env = env
        self.servers = simpy.Container(env, init=3, capacity=10)  # Initialize servers with a maximum capacity of 10
        self.energy_cost_model = energy_cost_model  # Inkluderer energy_cost_model
        self.elastic_data_center = elastic_data_center

    def increase_servers(self):
        yield self.servers.put(1)  # Add one server
        self.log_server_change("increased")
        # Add corresponding resources to ElasticDataCenter's pool
        self.elastic_data_center.m += ElasticDataCenter.RESOURCES_PER_SERVER
        self.elastic_data_center.n += 1  # Increasing server_capacity


    def decrease_servers(self):
        if self.servers.level > 0:
            yield self.servers.get(1)  # Remove one server
            self.log_server_change("decreased")
            # Remove corresponding resources from ElasticDataCenter's pool
            self.elastic_data_center.m = max(self.elastic_data_center.m - ElasticDataCenter.RESOURCES_PER_SERVER, 0)
            self.elastic_data_center.n -= 1  # Decreasing server_capacity

    def log_server_change(self, action):
       print(f"[Time {self.env.now:.2f}] Server {action}: Current servers = {self.elastic_data_center.m}, Energy Price = {self.energy_cost_model.elprice}")

    def condition_increase(self):
        users_per_server = self.elastic_data_center.k // self.elastic_data_center.n
        threshold_up = 3
        condition_result = (
            self.elastic_data_center.n <= 10
            and (self.energy_cost_model.elprice == "low" or self.energy_cost_model.elprice == "medium")
            and users_per_server >= threshold_up
        )
        
        print(f"users_per_server: {users_per_server}, servers: {self.elastic_data_center.n}, elprice: {self.energy_cost_model.elprice}, condition_result: {condition_result}")
        return condition_result


    def condition_decrease(self):
        users_per_server = self.elastic_data_center.k // self.elastic_data_center.n
        condition_result = (
            self.elastic_data_center.n > 2 
            and (self.energy_cost_model.elprice == "high")
            and users_per_server < 3
        )
        
        return condition_result

    def adjust_servers(self):
        while True:
            yield self.elastic_data_center.signal_up | self.elastic_data_center.signal_down
            if self.condition_increase():  
                yield self.env.process(self.increase_servers())
            elif self.condition_decrease():  
                yield self.env.process(self.decrease_servers())
            else:
                yield self.env.timeout(1)


# Model 3: Energy Cost Model
class EnergyCostModel:
    def __init__(self, env, durations, prices, elastic_dc_instance):
        self.env = env
        self.elprice = "low"
        self.current_price = prices['low']  # NOK/kWh
        self.durations = durations  # Duration for each price level
        self.prices = prices  # Prices for each level
        self.price_high_event = simpy.Event(env)
        self.price_low_event = simpy.Event(env)
        self.elastic_dc_instance = elastic_dc_instance
        self.total_cost = 0.0 # Initializing the total cost

    def wait_until(self, condition):
        while not condition():
            yield self.env.timeout(1)

    def price_change(self):
        while True:
            # Iterating through low, medium, high stages with their respective durations and prices
            for level, duration in self.durations.items():
                self.elprice = level
                self.current_price = self.prices[level]  # updating current price
                print(f"[Time {self.env.now}] Energy price changed to {self.elprice} ({self.current_price} NOK/kWh)")
                
                for _ in range(duration):  # Loop for each hour in duration
                    # Compute cost
                    users = self.elastic_dc_instance.k  # Example: Replace with the actual number of users at this time step
                    cost_at_t = (self.current_price  *
                                 ElasticDataCenter.USER_ENERGY_USAGE *
                                 (1/duration))  # Assuming time=1 for each loop iteration
                    self.total_cost += cost_at_t  # Accumulating the cost
                    yield self.env.timeout(1)  # wait for the next time step

            print(f"[Time {self.env.now}] Energy price changed to {self.elprice}")

    def print_total_cost(self):
        print(f"Total cost: {self.total_cost}")


def main():
    sim_duration = 10  # Total simulation duration (adjust as needed)
    lambda_ = 60  # Arrival rate (requests per unit of time)
    mu = 1  # Service rate (requests processed per unit of time)
    Qmin = 0.5  # Minimum value for Q
    n = 3  # Number of servers

    durations = {
        "low": 1,  # in hours
        "medium": 1,  # in hours
        "high": 2  # in hours
    }
    prices = {
        "low": 0.1,  # in NOK/kWh
        "medium": 1,  # in NOK/kWh
        "high": 5  # in NOK/kWh
    }

    env = simpy.Environment()

    # First, create an instance of ElasticDataCenter, as it doesn't depend on the other two instances.
    elastic_dc = ElasticDataCenter(env, n, lambda_, mu, Qmin, None)  # Temporarily setting the energy_cost_model to None
    # Create instances of the three models
    energy_cost_model = EnergyCostModel(env, durations, prices, elastic_dc)
    elastic_dc = ElasticDataCenter(env, n, lambda_, mu, Qmin, energy_cost_model)
    data_center = DataCenter(env, energy_cost_model, elastic_dc)


    # Define the simulation processes
    env.process(elastic_dc.generate_requests())
    env.process(data_center.adjust_servers())
    env.process(energy_cost_model.price_change())

    # Run the simulation
    env.run(until=sim_duration)

    # Print final results
    elastic_dc.print_final_rejects()

    # Print total cost
    energy_cost_model.print_total_cost()


if __name__ == "__main__":
    main()
