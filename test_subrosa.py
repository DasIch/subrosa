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

from subrosa import Share, add_share, recover_secret, split_secret


@composite
def threshold_and_shares(draw):
    threshold = draw(integers(min_value=2, max_value=255))
    shares = draw(integers(min_value=threshold, max_value=255))
    return threshold, shares


@pytest.mark.ci_only
@given(random_module(), binary(min_size=1), threshold_and_shares())
@settings(timeout=-1, max_examples=5)
def test_split_and_recover(_, secret, threshold_and_number_of_shares):
    """
    Tests whether the secret can be split and recovered for some random secret,
    threshold and share. This can take a long time to run (several minutes),
    for large thresholds or shares. For this reason this test is only executed
    when running on continous integration by default.

    Take a look at `test_split_and_recover_fast`, which always runs for a fast
    version of this test.
    """
    threshold, number_of_shares = threshold_and_number_of_shares

    shares = split_secret(secret, threshold, number_of_shares)
    subset = random.sample(shares, threshold)
    random.shuffle(subset)
    recovered_secret = recover_secret(subset)
    assert recovered_secret == secret


@pytest.mark.parametrize('secret', [
    b'secret',
    b'x' * 257
])
def test_split_and_recover_fast(secret):
    """
    Tests quickly whether the secret can be split and recovered. This test is
    not as exhaustive as `test_split_and_recover` but it hopefully still
    catches anything too obvious during local development.
    """
    shares = split_secret(secret, 2, 3)
    for i in range(2, 4):
        subset = random.sample(shares, i)
        random.shuffle(subset)
        recovered_secret = recover_secret(subset)
        assert recovered_secret == secret


class TestShare:
    def test_from_bytes(self):
        share = Share(2, 1, [2])
        binary = bytes(share)
        parsed_share = Share.from_bytes(binary)
        assert parsed_share.version == 1
        assert parsed_share._threshold == 2
        assert parsed_share.x == 1
        assert parsed_share._ys == [2]

    def test_from_bytes_invalid_version(self):
        share = Share(2, 1, [2])
        share.version = 0
        binary = bytes(share)
        with pytest.raises(NotImplementedError):
            Share.from_bytes(binary)

    def test_from_bytes_invalid_format(self):
        share = Share(2, 1, [2])
        binary = bytes(share)
        invalid_binary = binary[:-1]
        with pytest.raises(ValueError):
            Share.from_bytes(invalid_binary)


class TestSplitSecret:
    def test_empty_secret(self):
        with pytest.raises(ValueError):
            split_secret(b'', 2, 2)

    def test_threshold_less_than_2(self):
        with pytest.raises(ValueError):
            split_secret(b'a', 1, 2)

    def test_threshold_greater_than_255(self):
        with pytest.raises(ValueError):
            split_secret(b'a', 256, 256)

    def test_share_count_less_than_threshold(self):
        with pytest.raises(ValueError):
            split_secret(b'a', 3, 2)

    def test_share_count_greater_than_255(self):
        with pytest.raises(ValueError):
            split_secret(b'a', 2, 256)


class TestRecoverSecret:
    def test_empty_shares(self):
        with pytest.raises(ValueError):
            recover_secret([])

    def test_incompatible_shares_secret(self):
        shares_a = split_secret(b'a', 2, 3)
        shares_b = split_secret(b'ab', 2, 3)
        with pytest.raises(ValueError):
            recover_secret(shares_a[:1] + shares_b[:1])

    def test_incompatible_shares_threshold(self):
        shares_a = split_secret(b'a', 2, 3)
        shares_b = split_secret(b'a', 3, 3)
        with pytest.raises(ValueError):
            recover_secret(shares_a[:1] + shares_b[:2])

    def test_less_than_threshold(self):
        shares = split_secret(b'a', 2, 2)
        with pytest.raises(ValueError):
            recover_secret(shares[:1])


class TestAddShare:
    def test_new_share(self):
        shares = split_secret(b'secret', 2, 2)
        third_share = add_share(shares, 3)
        for share in shares:
            recovered_secret = recover_secret([share, third_share])
            assert recovered_secret == b'secret'

    def test_recreate_share(self):
        shares = split_secret(b'secret', 2, 2)
        for i, share in enumerate(shares, 1):
            recreated_share = add_share(shares, i)
            assert recreated_share._ys == share._ys

    def test_x_equals_0(self):
        """
        Make sure we don't leak the secret (which is at 0.)
        """
        shares = split_secret(b'secret', 2, 2)
        with pytest.raises(ValueError):
            add_share(shares, 0)

    def test_x_less_than_0(self):
        shares = split_secret(b'secret', 2, 2)
        with pytest.raises(ValueError):
            add_share(shares, -1)

    def test_x_greater_than_255(self):
        shares = split_secret(b'secret', 2, 2)
        with pytest.raises(ValueError):
            add_share(shares, 256)
