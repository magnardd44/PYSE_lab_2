import simpy
import random
import matplotlib.pyplot as plt
import numpy as np

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
        self.mos_scores = [] # MOS score for each user per hour
        self.q_values = [] # Q values for each user per hour
        self.hourly_mos_scores = []

    #def store_mos_scores_hourly(self):
    #    while True:
    #        yield self.env.timeout(60)  # wait for an hour
    #        if self.mos_scores:
    #            selected_mos = random.choice(self.mos_scores)
    #            self.hourly_mos_scores.append(selected_mos)
    #        else:
    #            self.hourly_mos_scores.append(1)

    def store_mos_scores_hourly(self):
        while True:
            yield self.env.timeout(60)  # wait for an hour
            avg_mos = sum(self.mos_scores) / len(self.mos_scores) if self.mos_scores else 0
            self.hourly_mos_scores.append(avg_mos)
            self.mos_scores = []  # reset the mos_scores for the next hour


    def generate_requests(self):
        k = 0  # Initialize k
        while True:
            # Generate an inter-arrival time from an exponential distribution
            interarrival_time = random.expovariate(self.lambda_)

            # Yield an event for the next request arrival
            yield self.env.timeout(interarrival_time)

            # Calculate Q based on the described logic - fair share
            Q = min(1, self.m / self.k) if self.k > 0 else 1
            
            potential_users_per_server = (self.k + 1) / self.n if self.n > 0 else float('inf')

            # Check if Q is greater than Qmin
            if Q > self.Qmin and potential_users_per_server <= 4.5:
                    if self.m > 0:
                        k += 1
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
        print(f"User3 with k={self.k} and Q={Q} handling request at time {self.env.now}")

        # Simulate the processing time
        yield self.env.timeout(1 / self.mu)  # Representing streaming duration as per 1/mu

        # Get the energy cost for processing this user's request
        user_energy_usage = ElasticDataCenter.USER_ENERGY_USAGE
        self.energy_cost_model.calculate_cost(self.k, user_energy_usage)

        print(f"User3 with k={self.k} and Q={Q} finished processing at time {self.env.now}")
        print(f"active users={self.k} Server Pool Count: {self.m}, Q: {Q}")

        # Release the resource
        self.m += 1  # Increase the number of available resources
        self.k -= 1  # Decrease the number of active users

        # Signal that a resource has been released (if any process is waiting for this)
        self.signal_up.succeed()  
        self.signal_up = simpy.Event(self.env)

         # Calculate MOS score
        mos_score = self.calculate_MOS(Q)
        print(f"User3 with k={self.k} and Q={Q} has MOS score: {mos_score} at time {self.env.now}")

        # Store the MOS score and Q value
        self.mos_scores.append(mos_score)
        self.q_values.append(Q)


    @staticmethod
    def calculate_MOS(Q):
        """
        Calculate the MOS score based on the Q factor using the given step function.

        Parameters:
        - Q: quality factor

        Returns:
        int: MOS score (1-5)
        """
        # Threshold values
        q = [0.0, 0.5, 0.6, 0.8, 0.9, 1.0]

        # Define MOS score
        for i in range(1, 6):
            if q[i-1] < Q <= q[i]:
                return i
    
        # Default MOS score if Q does not match any condition
        # (not needed if Q is always within the predefined thresholds)
        return 1
    

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
    def __init__(self, env, durations, prices):
        self.env = env
        self.elprice = "low"
        self.current_price = prices['low']  # NOK/kWh
        self.durations = durations  # Duration for each price level
        self.prices = prices  # Prices for each level
        self.price_high_event = simpy.Event(env)
        self.price_low_event = simpy.Event(env)
        self.total_cost = 0  # Initialize total cost
        self.price_table = []  # Initialize an empty list to store prices

    def calculate_cost(self, k, user_energy_usage):
        cost = self.current_price * k * user_energy_usage
        self.total_cost = cost


    def wait_until(self, condition):
        while not condition():
            yield self.env.timeout(1)


    def price_change(self):
        while True:
            # Iterating through low, medium, high stages with their respective durations and prices
            for level, duration in self.durations.items():
                self.elprice = level
                low, high = self.prices[level]
                self.current_price = random.uniform(low, high)  # Generate a random price within the range
                self.price_table.append((self.env.now, self.current_price))  # Store the price and the current time in the table
                print(f"[Time {self.env.now}] Energy price changed to {self.elprice} ({self.current_price:.2f} NOK/kWh)")
                yield self.env.timeout(duration)  # Holding the price for the defined duration
    
            print(f"[Time {self.env.now}] Energy price changed to {self.elprice}")



    def get_avg_price_per_min(self, end_time):
        min = 0  
        avg_price_per_min = []  

        while min*60 < end_time:  # Considering the end_time in minutes
            # Filtering prices that are within the current min (time in minutes)
            prices_this_min = [price for time, price in self.price_table if min*60 <= time < (min + 1)*60] 

            if prices_this_min:
                avg_price = sum(prices_this_min) / len(prices_this_min)
            else:
                avg_price = 0  

            avg_price_per_min.append((min, avg_price))
            print(f"Average price during min {min} - {min+1}: {avg_price:.2f} NOK/kWh")

            min += 1

        return avg_price_per_min


    #def price_change(self):
    #    while True:
    #        # Iterating through low, medium, high stages with their respective durations and prices
    #        for level, duration in self.durations.items():
    #            self.elprice = level
    #            self.current_price = self.prices[level]  # updating current price
    #            self.price_table.append((self.env.now, self.current_price))  # Store the price and the current time in the table
    #            print(f"[Time {self.env.now}] Energy price changed to {self.elprice} ({self.current_price} NOK/kWh)")
    #            yield self.env.timeout(duration)  # Holding the price for the defined duration
    #
    #        print(f"[Time {self.env.now}] Energy price changed to {self.elprice}")


def main():
    sim_duration = 24*60  # Total simulation duration (adjust as needed)
    lambda_ = 60 # Arrival rate (requests per unit of time)
    mu = 1  # Service rate (requests processed per unit of time)
    Qmin = 0.5  # Minimum value for Q
    n = 3  # Number of servers

    durations = {
        "low": 1,  # in hours
        "medium": 1,  # in hours
        "high": 2  # in hours
    }
    prices = {
        "low": (0.1, 0.99),  # in NOK/kWh
        "medium": (1, 4.99),  # in NOK/kWh
        "high": (5, 6)   # in NOK/kWh
        #"low": (0.1),  # in NOK/kWh
        #"medium": (1),  # in NOK/kWh
        #"high": (5)   # in NOK/kWh
    }

    env = simpy.Environment()

    # Create instances of the three models
    energy_cost_model = EnergyCostModel(env, durations, prices)
    elastic_dc = ElasticDataCenter(env, n, lambda_, mu, Qmin, energy_cost_model)
    data_center = DataCenter(env, energy_cost_model, elastic_dc)


    # Define the simulation processes
    env.process(elastic_dc.generate_requests())
    env.process(data_center.adjust_servers())
    env.process(energy_cost_model.price_change())
    env.process(elastic_dc.store_mos_scores_hourly())


    # Run the simulation
    env.run(until=sim_duration)

    # Print final results
    elastic_dc.print_final_rejects()


    # Compute and print the average MOS score and Q value for each hour
    if elastic_dc.mos_scores and elastic_dc.q_values:  # Check if lists are not empty
        avg_mos_score = sum(elastic_dc.mos_scores) / len(elastic_dc.mos_scores)
        avg_q_value = sum(elastic_dc.q_values) / len(elastic_dc.q_values)
        print(f"Average MOS score: {avg_mos_score:.2f}")
        print(f"Average Q value: {avg_q_value:.2f}")
    else:
        print("No MOS scores or Q values to average.")


    # Retrieve and display the total energy cost
    print(f"Total Energy Cost: {energy_cost_model.total_cost} NOK")

    return energy_cost_model.price_table, elastic_dc.mos_scores, elastic_dc.q_values, elastic_dc.hourly_mos_scores

if __name__ == "__main__":
    price_table, mos_scores, q_values, hourly_mos_scores = main()

    times, prices = zip(*price_table)

#time_array = np.array([i for i in range(24*60)])
#mos_array = np.array([item for item in mos_scores])
#cost_array = np.array([item for item in prices])
 # Ensure arrays are of correct size
    hourly_mos_scores = hourly_mos_scores
    prices = prices[:23]
    
    time_array = np.array([i for i in range(len(hourly_mos_scores))])  # based on actual data size


#Plot price level over time
plt.plot(time_array, prices)
plt.xlabel("minutes")
plt.ylabel("Price in NOK")
plt.show()

#Plot quality level over time
plt.plot(time_array, prices)
plt.xlabel("minutes")
plt.ylabel("Quality")
plt.show()


# Plot price and quality together over time
fig, ax1 = plt.subplots()
color = 'tab:red'
ax1.set_xlabel('time (m)')
ax1.set_ylabel('Quality', color=color)
ax1.plot(time_array, hourly_mos_scores, color=color)
ax1.tick_params(axis='y', labelcolor=color)
ax2 = ax1.twinx()
color = 'tab:blue'
ax2.set_ylabel('price', color=color)
ax2.plot(time_array,prices, color=color)
ax2.tick_params(axis='y', labelcolor=color)
fig.tight_layout()
plt.show()