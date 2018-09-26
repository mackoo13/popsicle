from sklearn.base import clone
import numpy as np
from popsicle.ml_utils.data_set import DataSet
from popsicle.ml_utils.ml_utils import regr_score


class WeightsTuner:
    def __init__(self, data: DataSet, regr):
        self.data = data
        self.regr = regr

        self.population = []
        self.best_weights = None
        self.n_generations = 10
        self.population_size = 10
        self.alpha = 0.2
        self.init_mean = 1
        self.init_std = 0.5

        self.__random_init()

    def fit(self):
        print('Weights tuning (using genetic implementation)')
        for gen in range(self.n_generations):
            print('\tGeneration ' + str(gen) + '/' + str(self.n_generations))

            for i in range(self.population_size):
                for j in range(i):
                    c1 = self.__ith_weights(i)
                    c2 = self.__ith_weights(j)
                    weights = self.__random_weights_between(c1, c2)
                    self.__append_chromosome(weights)

                mutated_weights = self.__mutate(self.__ith_weights(i))
                mutated_score = self.__weight_score(mutated_weights)
                if mutated_score > self.__ith_score(i):
                    self.population[i] = (mutated_score, mutated_weights)

            self.__natural_selection()

        self.best_weights = self.__ith_weights(0)

    # PRIVATE MEMBERS

    def __append_chromosome(self, weights):
        """
        Adds a new vector to the population
        """
        self.population.append((self.__weight_score(weights), weights))

    def __weight_score(self, weights):
        """
        Calculates the score of a vector of weights
        """
        multiplied_data = DataSet(
            np.multiply(self.data.x, weights),
            self.data.y
        )
        return regr_score(multiplied_data, clone(self.regr))

    def __ith_weights(self, i):
        """
        Return the i-th vector of weights in the population
        """
        return self.population[i][1]

    def __ith_score(self, i):
        """
        Return the score of the i-th vector in the population
        """
        return self.population[i][0]

    def __mutate(self, weights):
        """
        Apply a random mutation to a chromosome
        """
        new_weights = weights.copy()
        for nmut in range(2):
            imut = np.random.randint(len(weights))
            new_weights[imut] = np.random.normal(self.init_mean, self.init_std)

        return new_weights

    def __natural_selection(self):
        """
        Eliminate weaker chromosomes from the population
        """
        self.population = sorted(self.population, key=lambda q: q[0], reverse=True)[:self.population_size]

    def __print_population(self):
        """
        Debug
        """
        for s, c in self.population:
            print(round(s, 2), '\t\t', [round(q, 2) for q in c])

    def __random_weights_between(self, c1, c2):
        """
        Generate an offspring of c1 and c2.
        """
        mins = np.minimum(c1, c2)
        maxs = np.maximum(c1, c2)

        margin = self.alpha * (maxs - mins)
        low = np.maximum(mins - margin, np.zeros(mins.shape))
        high = maxs + margin
        return np.random.uniform(low, high)

    def __random_init(self):
        """
        Random initialisation of the population
        """
        weights = np.array([1] * self.data.x.shape[1])
        self.population = [(self.__weight_score(weights), weights)]

        for i in range(10 * self.population_size):
            weights = np.random.normal(self.init_mean, self.init_std, size=self.data.x.shape[1])
            self.__append_chromosome(weights)

        self.__natural_selection()
