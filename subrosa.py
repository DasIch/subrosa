"""
    subrosa
    ~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from random import SystemRandom

from gf256 import GF256


__version__ = '0.1.0'
__version_info__ = (0, 1, 0)


_random = SystemRandom()


def _create_random_polynomial(degree, free_coefficient):
    coefficients = [GF256(free_coefficient)]
    coefficients.extend([GF256(_random.randrange(256)) for _ in range(degree)])
    return coefficients


def _evaluate_polynomial(coefficients, x):
    return sum(
        (
            coefficient * x ** GF256(exponent)
            for exponent, coefficient in enumerate(coefficients)
        ),
        GF256(0)
    )


def _split_secret_byte(secret, threshold, shares):
    coefficients = _create_random_polynomial(threshold - 1, secret)
    return [
        (x, int(_evaluate_polynomial(coefficients, GF256(x))))
        for x in range(1, shares + 1)
    ]


def _lagrange_interpolation(points, x):
    y = GF256(0)
    for j in range(len(points)):
        l = GF256(1)
        for m in range(len(points)):
            if m != j:
                l *= (x - points[m][0]) / (points[j][0] - points[m][0])
        y += points[j][1] * l
    return y


def _recover_secret_byte(shares):
    return int(_lagrange_interpolation(
        [(GF256(x), GF256(y)) for x, y in shares],
        GF256(0))
    )
