from asyncore import write
from unittest import result
import simpy
import random
import pandas as pd
import csv

# Class for storing global parameters
# I won't instantiate this, it's just for storing purposes
# In this simulation, I am treating the survivor count as groups of 4
# for the sake of simplicity since 4 survivors and 1 killer are required
# for each DBD Match to take place
class g:
    survivor_inter = 5
    mean_match_time = 30
    number_of_killers = 2
    sim_duration = 120
    number_of_runs = 10


# Class representing our survivors coming in to play some Dead By Daylight!
# Only contains a constructor to set up the survivor ID and the queue time
class Survivor_Logon:
    def __init__(self, p_id):
        self.id = p_id
        self.q_time_match = 0

# Class for the Matchmaker Model
class Matchmaker_Model:
    # This constructor sets up the env, the survivor counter and the resources
    def __init__(self, run_number):
        self.env = simpy.Environment()
        self.survivor_counter = 0

        self.killer = simpy.Resource(self.env, capacity = g.number_of_killers)

        self.run_number = run_number

        self.mean_q_time_match = 0

        self.results_df = pd.DataFrame()
        self.results_df["P_ID"] = []
        self.results_df["Start_Q_Match"] = []
        self.results_df["End_Q_Match"] = []
        self.results_df["q_time_match"] = []
        self.results_df.set_index("P_ID", inplace = True)

    # A method that generates survivors to enter Matchmaking queue
    def generate_survivor_logon(self):
        # Loop to keep generating until end of the sim
        while True:
            # Increment the survivor counter by 1
            self.survivor_counter += 1
            #g.number_of_killers += 1

            # Create a new survivor from the Survivor_Logon class and
            # give the survivor an ID determined by the survivor counter
            sl = Survivor_Logon(self.survivor_counter)

            # Get the SimPy env to run the match_found method with this survivor group
            self.env.process(self.match_found(sl))

            # Randomly sample the time to the next survivor group queueing up for a match
            sampled_interarrival = random.expovariate(1.0/ g.survivor_inter)

            # Freeze this function until that time has elapsed
            yield self.env.timeout(sampled_interarrival)

    # A method that models the processes for finding a Match and playing the game
    # A survivor group needs to be passed into this
    def match_found(self, survivor):
        # Record and print the time the survivor group started queueing for a match
        start_q_match = self.env.now
        print("Survivor group ", survivor.id, " started queuing at ", self.env.now, sep ="")

        # Request a killer
        with self.killer.request() as req:
            # Freeze the function until the request for a killer can be met
            yield req

            # Record the time the survivor finished queuing for a Match
            end_q_match = self.env.now

            # Calculate the time this survivor spent queuing for a Match
            # and store in the survivor's attribute
            survivor.q_time_match = end_q_match - start_q_match

            # Store the start and end queue times alongside the survivor ID in
            # the Pandas DataFrame of the Matchmaker_Model class
            df_to_add = pd.DataFrame({"P_ID":[survivor.id],
                                        "Start_Q_Match":[start_q_match],
                                        "End_Q_Match":[end_q_match],
                                        "q_time_match":[survivor.q_time_match]})
            df_to_add.set_index("P_ID", inplace=True)
            self.results_df = self.results_df.append(df_to_add)

            # Print the time the survivor group found a game
            print("Survivor group ", survivor.id, " found a match at ", self.env.now, sep="")

            # Randomly sample the time the survivors will spend in a match
            # The mean is stored in the g class
            sampled_match_time = random.expovariate(1.0/ g.mean_match_time)

            # Freeze this function until the end of the match
            yield self.env.timeout(sampled_match_time)

    # Method that calculates the mean queuing time for a Match
    def calc_mean_q_time_match(self):
        self.mean_q_time_match = self.results_df["q_time_match"].mean()

    # A method to write the results to file
    def write_run_results(self):
        with open("sim_results.csv", "a") as f:
            writer = csv.writer(f, delimiter= ",")
            results_to_write = [self.run_number,
                                self.mean_q_time_match]
            writer.writerow(results_to_write)



    # The run method starts up the generators and tells SimPy to start
    # running the environment for the duration specified in the g class
    def run(self):
        self.env.process(self.generate_survivor_logon())
        self.env.run(until=g.sim_duration)
        self.calc_mean_q_time_match()
        self.write_run_results()

class Sim_Results_Calculator:
    def __init__(self):
        self.sim_results_df = pd.DataFrame()

    # A method to read in the sim results and print them
    def print_sim_results(self):
        print("RESULTS")
        print("-------")

        # Read results from each run
        self.sim_results_df = pd.read_csv("sim_results.csv")

        # Calculate the mean of the runs
        sim_mean_q_time_match = (self.sim_results_df["Mean_q_time_match"].mean())

        print("Mean Queuing Time for Matches over the span of the Sim: ",
        round(sim_mean_q_time_match, 2))

# Create a file to store results
with open("sim_results.csv", "w") as f:
    writer = csv.writer(f, delimiter=",")
    column_headers = ["Run #", "Mean_q_time_match"]
    writer.writerow(column_headers)

# Everything above is definition and set up code

# For the number of runs specified in the g class, create an instance of the
# Matchmaker_Model class, and call its run method

for run in range(g.number_of_runs):
    print("Run ", run+1, " of ", g.number_of_runs, sep="")
    my_matchmaker_model = Matchmaker_Model(run)
    my_matchmaker_model.run()
    print()

my_sim_results_calculator = Sim_Results_Calculator()
my_sim_results_calculator.print_sim_results()