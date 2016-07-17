"""
    test_subrosa
    ~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import random

from hypothesis import given, settings
from hypothesis.strategies import data, integers, random_module

from subrosa import _recover_secret_byte, _split_secret_byte


@given(data())
@settings.get_profile('slow_test')
def test_secret_byte(data):
    data.draw(random_module())
    secret = data.draw(integers(min_value=0, max_value=255))
    threshold = data.draw(integers(min_value=2, max_value=255))
    number_of_shares = data.draw(integers(min_value=threshold, max_value=255))

    shares = _split_secret_byte(secret, threshold, number_of_shares)
    subset = random.sample(shares, threshold)
    random.shuffle(subset)
    recovered_secret = _recover_secret_byte(subset)
    assert secret == recovered_secret
