"""
    test_subrosa
    ~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import random

import pytest
from hypothesis import given, settings
from hypothesis.strategies import binary, composite, integers, random_module

from subrosa import recover_secret_bytes, split_secret_bytes


@composite
def threshold_and_shares(draw):
    threshold = draw(integers(min_value=2, max_value=255))
    shares = draw(integers(min_value=threshold, max_value=255))
    return threshold, shares


@pytest.mark.parametrize('secret', [
    b'secret',
    b'x' * 257
])
def test_secret_bytes_fast(secret):
    shares = split_secret_bytes(secret, 2, 3)
    for i in range(2, 4):
        subset = random.sample(shares, i)
        random.shuffle(subset)
        recovered_secret = recover_secret_bytes(subset)
        assert recovered_secret == secret


@pytest.mark.ci_only
@given(random_module(), binary(min_size=1), threshold_and_shares())
@settings(timeout=-1, max_examples=5)
def test_secret_bytes(_, secret, threshold_and_number_of_shares):
    threshold, number_of_shares = threshold_and_number_of_shares

    shares = split_secret_bytes(secret, threshold, number_of_shares)
    subset = random.sample(shares, threshold)
    random.shuffle(subset)
    recovered_secret = recover_secret_bytes(subset)
    assert recovered_secret == secret


class TestSplitSecretBytes:
    def test_empty_secret(self):
        with pytest.raises(ValueError):
            split_secret_bytes(b'', 2, 2)

    def test_threshold_less_than_2(self):
        with pytest.raises(ValueError):
            split_secret_bytes(b'a', 1, 2)

    def test_threshold_greater_than_255(self):
        with pytest.raises(ValueError):
            split_secret_bytes(b'a', 256, 256)

    def test_share_count_less_than_threshold(self):
        with pytest.raises(ValueError):
            split_secret_bytes(b'a', 3, 2)

    def test_share_count_greater_than_255(self):
        with pytest.raises(ValueError):
            split_secret_bytes(b'a', 2, 256)


class TestRecoverSecretBytes:
    def test_empty_shares(self):
        with pytest.raises(ValueError):
            recover_secret_bytes([])

    def test_unsupported_version(self):
        shares = split_secret_bytes(b'a', 2, 3)
        shares[0] = b'\x00' + shares[0][1:]
        with pytest.raises(ValueError):
            recover_secret_bytes(shares)

    def test_incomplete_share(self):
        shares = split_secret_bytes(b'a', 2, 3)
        shares[0] = shares[0][:-1]
        with pytest.raises(ValueError):
            recover_secret_bytes(shares)

    def test_incompatible_shares_secret(self):
        shares_a = split_secret_bytes(b'a', 2, 3)
        shares_b = split_secret_bytes(b'ab', 2, 3)
        with pytest.raises(ValueError):
            recover_secret_bytes(shares_a[:1] + shares_b[:1])

    def test_incompatible_shares_threshold(self):
        shares_a = split_secret_bytes(b'a', 2, 3)
        shares_b = split_secret_bytes(b'a', 3, 3)
        with pytest.raises(ValueError):
            recover_secret_bytes(shares_a[:1] + shares_b[:2])

    def test_less_than_threshold(self):
        shares = split_secret_bytes(b'a', 2, 2)
        with pytest.raises(ValueError):
            recover_secret_bytes(shares[:1])
