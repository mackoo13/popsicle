from sklearn.base import clone
import numpy as np

from ml_utils.ml_utils import calc_score


class CoeffsLearner:
    def __init__(self, x, y, df, clf):
        self.x = x
        self.y = y
        self.df = df
        self.population = []
        self.clf = clf
        self.coeffs = None

    def append_chromosome(self, scores, coeffs):
        scores.append((self.coeff_score(coeffs), coeffs))

    def coeff_score(self, coeffs):
        x2 = np.multiply(self.x, coeffs)
        return calc_score(x2, self.y, self.df, clone(self.clf))

    def fit(self):
        n_gen = 10
        population = 10
        alpha = 0.2

        coeffs = [1] * self.x.shape[1]
        scores = [(self.coeff_score(coeffs), coeffs)]

        for i in range(10 * population):
            coeffs = np.random.normal(1, .5, size=self.x.shape[1])
            scores.append((self.coeff_score(coeffs), coeffs))

        scores = sorted(scores, key=lambda q: q[0], reverse=True)[:population]

        for s, c in scores:
            print(round(s, 2), '\t\t', [round(q, 2) for q in c])

        for gen in range(n_gen):
            print('gen', gen)

            for i in range(population):
                for j in range(i):
                    c1 = scores[i][1]
                    c2 = scores[j][1]
                    coeffs = np.random.uniform(c1 - alpha * (c2 - c1), c2 + alpha * (c2 - c1))
                    scores.append((self.coeff_score(coeffs), coeffs))

                new_coeffs = scores[i][1].copy()
                for nmut in range(2):
                    imut = np.random.randint(len(coeffs))
                    new_coeffs[imut] = np.random.normal(1, .5)

                new_score = self.coeff_score(new_coeffs)
                if new_score > scores[i][0]:
                    scores[i] = (new_score, new_coeffs)

            scores = sorted(scores, key=lambda q: q[0], reverse=True)[:10]
            for s, c in scores:
                print(round(s, 2), '\t\t', [round(q, 2) for q in c])

        self.coeffs = scores[0][1]
