#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#####################################
### Library imports for the model ###
#####################################

from copy import deepcopy
from random import choice, sample, random, seed
from itertools import combinations
import matplotlib.pyplot as plt


###############################
### Change these parameters ###
###############################

NUM_TIMESTEPS = 100 # 500
NUM_RESISTANCE_TYPES = 3
POPULATION_SIZE = 5000
PROBABILITY_MUTATION = 0.2 # 0.02
PROBABILITY_GENERAL_RECOVERY = 0.01
PROBABILITY_SPREAD = 1
NUM_SPREAD_TO = 2

TOGGLE_OUR_DESIGN = True


#################################################
### Internal parameters and derived constants ###
#################################################

RANDOM_SEED = 0

REPORT_PROGRESS = True
REPORT_PERCENTAGE = 5
PRINT_DATA = True
ANIMATE_GRAPH = True
GRAPH_TYPE = "stackplot"  # line, stackplot (default)
OUTPUT_PADDING = len(str(POPULATION_SIZE))

# Only import the niche drawnow library if it is needed, to allow use even if
# someone cannot install it, just with fewer features
if ANIMATE_GRAPH:
    from drawnow import drawnow

REPORT_MOD_NUM = int(NUM_TIMESTEPS / (100/REPORT_PERCENTAGE))
RESISTANCE_NAMES = [str(i+1) for i in range(NUM_RESISTANCE_TYPES)]
RESISTANCE_COMBINATIONS = []
for i in reversed(range(len(RESISTANCE_NAMES))):
    RESISTANCE_COMBINATIONS.extend([",".join(map(str,j))
                            for j in combinations(RESISTANCE_NAMES, i+1)])
RESISTANCE_COMBINATIONS.append("#")

OUR_DETECTOR, OTHER_RESISTANCES = RESISTANCE_NAMES[0], RESISTANCE_NAMES[1:]


#######################################
### Objects and logic for the model ###
#######################################

class Person:
    def __init__(self):
        """Everybody starts uninfected with no resistant strains in the model"""
        self.infected = False
        self.resistances = {resistance: False for resistance in RESISTANCE_NAMES}

    def mutate_infections(self):
        """Make a person resistant to each antibiotic with a set probability"""
        for resistance in RESISTANCE_NAMES:
            if decision(PROBABILITY_MUTATION):
                self.infected = True
                self.resistances[resistance] = True

    def recover_from_infection(self):
        """Recover the person, returning them to their default state; totally
        uninfected with no resistances"""
        self.__init__()

    def treat_infection(self, antibiotic_name):
        """Treat the infection with an antibiotic - if the infection is
        resistant to it, do nothing, otherwise, kill the infection and all
        other resistances it included"""
        if self.resistances[antibiotic_name] == False:
            self.recover_from_infection()

    def spread_infection(self, other):
        """Give any present resistant strains from the current object to the
        other object"""
        for resistance, present in self.resistances.items():
            if present:
                other.resistances[resistance] = True

    def get_resistances_name(self):
        """Get a canonical name for the present resistances"""
        string = ",".join([k for k, v in self.resistances.items() if v])
        if string == "":
            return "#"
        return string

    def __repr__(self):
        """Return a string representation of the class"""
        if self.infected:
            return "Infected with {}".format(self.get_resistances_name())
        return "Not infected"


class Model:
    def __init__(self, population=None):
        """Start the model with a population of uninfected people, or a custom
        population provided as a parameter"""
        if population is None:
            self.population = [Person() for _ in range(POPULATION_SIZE)]
        else:
            self.population = population

        # Abstract away all the data handling into another class to avoid
        # cluttering up the model logic
        self.data_handler = DataHandler()

        self.ys_data = [[0] * NUM_TIMESTEPS for _ in range(2 ** NUM_RESISTANCE_TYPES)]

    def run(self):
        """Simulate a number of timesteps within the model"""
        for i in range(NUM_TIMESTEPS):

            # Record data about the proportions of strains prevalence within
            # the population
            self.data_handler.process_timestep_data(
                self.get_infection_statistics().values()
            )

            # For each person in the population
            for person in self.population:
                # Allow for recovery from their infection
                if decision(PROBABILITY_GENERAL_RECOVERY):
                    person.recover_from_infection()

                # Allow for mutation to a resistant strain
                if decision(PROBABILITY_MUTATION):
                    person.mutate_infections()

                # Treat with a random antibiotic (which are named the same
                # as the strains which are resistant to them)
                if person.infected:
                    if TOGGLE_OUR_DESIGN:
                        # Apply our detection method (identifying a) to improve
                        # success at treatment stage
                        if person.resistances[OUR_DETECTOR]:
                            antibiotic = choice(OTHER_RESISTANCES)
                        else:
                            antibiotic = OUR_DETECTOR
                    else:
                        # Randomly choose what to treat with
                        antibiotic = choice(RESISTANCE_NAMES)

                    person.treat_infection(antibiotic)

            # Spread the infection strains throughout the population
            # We need a deepcopy operation, to prevent someone who has just
            # been spread to in this timestep spreading the thing they've
            # just received, so technically don't have yet
            updated_population = deepcopy(self.population)
            for person in self.population:
                if person.infected and decision(PROBABILITY_SPREAD):
                    for receiver in sample(updated_population, NUM_SPREAD_TO):
                        person.spread_infection(receiver)
            self.population = updated_population[:]


    def get_infection_statistics(self):
        """Get the percentage infected with each type of bacteria"""
        infections = {name:0 for name in RESISTANCE_COMBINATIONS}
        for person in self.population:
            infections[person.get_resistances_name()] += 1
        return infections

    def __repr__(self):
        """Return a string encoding the percentage of people infected by
        each anti-biotic resistant bacteria"""
        infection_strings = ""
        for k,v in self.get_infection_statistics():
            infection_strings += "{}% {}".format(v, k)
        return ",".join(infection_strings)


def decision(probability):
    """Get a boolean value with a given probability"""
    return random() < probability


###############################################
### Data handler and renderer for the model ###
###############################################

class DataHandler:
    def __init__(self):
        """Initialise the data handler for the model as storing data
        in an appropriate structure"""
        self.time = []
        self.ys_data = [[] for _ in range(2 ** NUM_RESISTANCE_TYPES)]

        self.timestep = 0

    def draw_full_graph(self):
        """Draw a graph of all of the data in the graph"""
        DataRenderer.draw_full_graph(
                            self.time, self.ys_data, RESISTANCE_COMBINATIONS)

    def _print_current_data(self):
        """Print the values of the current state of the simulation"""
        # TODO
        items = []
        for i,label in enumerate(RESISTANCE_COMBINATIONS):
            items.append("{}: {}".format(
                RESISTANCE_COMBINATIONS[i],
                str(round(self.ys_data[i][-1], 2)).ljust(OUTPUT_PADDING)
            ))
        print(", ".join(items))

    def _report_model_state(self):
        """Report the model's state through any mechanism set in parameters"""
        if self.timestep % REPORT_MOD_NUM == 0:
            if REPORT_PROGRESS and not PRINT_DATA:
                print("{}% complete".format(int(
                    self.timestep / int(NUM_TIMESTEPS / 10) * 10
                )))

            if PRINT_DATA:
                if REPORT_PROGRESS:
                    # Display it on the same line for ease of reading
                    print("{}% complete".format(str(int(
                        self.timestep / int(NUM_TIMESTEPS / 10) * 10
                    )).ljust(2)), end=" - ")
                self._print_current_data()

        if ANIMATE_GRAPH:
            DataRenderer.animate_current_graph(
                            self.time, self.ys_data, RESISTANCE_COMBINATIONS)

    def process_timestep_data(self, infection_percentages):
        """Store the current timestep's data into the appropriate data
        structures"""
        for j,data_point in enumerate(infection_percentages):
            self.ys_data[j].append(data_point)
        self.time.append(self.timestep)

        self.timestep += 1
        # Report the model's state through any mechanism set in parameters
        self._report_model_state()


class DataRenderer:
    @staticmethod
    def _draw_graph(time, ys_data, labels):
        """Actually draw the graph via matplotlib"""
        if GRAPH_TYPE == "line":
            # line graph
            for i in range(len(ys_data)):
                plt.plot(time, ys_data[i], label=labels[i])
        else:
            # stackplot as default
            plt.stackplot(time, *ys_data, labels=labels)

    @staticmethod
    def _graph_settings():
        """Add settings for the graph, e.g. axis labels and legend"""
        plt.title('Resistance simulation')
        plt.legend(loc='upper right')
        plt.xlabel("Time / timesteps")
        plt.ylabel("# People")

    @staticmethod
    def draw_full_graph(time, ys_data, labels):
        """Draw and show the graph with all the data and legend once"""
        DataRenderer._draw_graph(time, ys_data, labels)
        DataRenderer._graph_settings()
        plt.show()

    @staticmethod
    def animate_current_graph(time, ys_data, labels):
        """Draw a graph up to the current state of the simulation"""
        drawnow(lambda: DataRenderer._draw_graph(time, ys_data, labels))


if __name__ == "__main__":
    # Seed the random number generator
    if RANDOM_SEED is not None:
        seed(RANDOM_SEED)

    # Enable interactivity in matplotlib figures
    plt.ion()

    # Create and run the model
    m = Model()
    m.run()

    if not ANIMATE_GRAPH:
        # Finally show the full simulation graph
        m.data_handler.draw_full_graph()

    # Don't immediately close when the simulation is done
    input("Press any key to exit: ")
