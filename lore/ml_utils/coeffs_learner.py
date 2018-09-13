from sklearn.base import clone
import numpy as np

from ml_utils.df_utils import DataSet
from ml_utils.ml_utils import calc_score


class CoeffsLearner:
    def __init__(self, data: DataSet, clf):
        self.data = data
        self.clf = clf

        self.population = []
        self.best_coeffs = None
        self.n_generations = 3
        self.population_size = 10
        self.alpha = 0.2
        self.init_mean = 1
        self.init_std = 0.5

        self.__random_init()

    def fit(self):
        for gen in range(self.n_generations):
            print('gen', gen)

            for i in range(self.population_size):
                for j in range(i):
                    c1 = self.__ith_coeffs(i)
                    c2 = self.__ith_coeffs(j)
                    coeffs = self.__random_coeffs_between(c1, c2)
                    self.__append_chromosome(coeffs)

                mutated_coeffs = self.__mutate(self.__ith_coeffs(i))
                mutated_score = self.__coeff_score(mutated_coeffs)
                if mutated_score > self.__ith_score(i):
                    self.population[i] = (mutated_score, mutated_coeffs)

            self.__natural_selection()

        self.best_coeffs = self.__ith_coeffs(0)

    # PRIVATE MEMBERS

    def __append_chromosome(self, coeffs):
        self.population.append((self.__coeff_score(coeffs), coeffs))

    def __coeff_score(self, coeffs):
        multiplied_data = DataSet(
            np.multiply(self.data.x, coeffs),
            self.data.y,
            self.data.df
        )
        return calc_score(multiplied_data, clone(self.clf))

    def __ith_coeffs(self, i):
        return self.population[i][1]

    def __ith_score(self, i):
        return self.population[i][0]

    def __mutate(self, coeffs):
        new_coeffs = coeffs.copy()
        for nmut in range(2):
            imut = np.random.randint(len(coeffs))
            new_coeffs[imut] = np.random.normal(self.init_mean, self.init_std)

        return new_coeffs

    def __natural_selection(self):
        self.population = sorted(self.population, key=lambda q: q[0], reverse=True)[:self.population_size]

    def __print_population(self):
        for s, c in self.population:
            print(round(s, 2), '\t\t', [round(q, 2) for q in c])

    def __random_coeffs_between(self, c1, c2):
        margin = self.alpha * (c2 - c1)
        low = np.maximum(c1 - margin, np.zeros(c1.shape))
        high = c2 + margin
        return np.random.uniform(low, high)

    def __random_init(self):
        coeffs = np.array([1] * self.data.x.shape[1])
        self.population = [(self.__coeff_score(coeffs), coeffs)]

        for i in range(10 * self.population_size):
            coeffs = np.random.normal(self.init_mean, self.init_std, size=self.data.x.shape[1])
            self.__append_chromosome(coeffs)

        self.__natural_selection()
