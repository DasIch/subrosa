"""
    subrosa
    ~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import struct
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


def _add_share_byte(shares, x):
    points = [(GF256(x), GF256(y)) for x, y in shares]
    return int(_lagrange_interpolation(points, GF256(x)))


class Share:
    """
    Represents a share of a secret.

    Can be turned into a byte string using :func:`bytes`. Use this along with
    :meth:`from_bytes` to store shares.
    """
    version = 1

    @classmethod
    def from_bytes(cls, bytestring):
        """
        Returns a `Share` instance given a byte string representation of a
        share.

        This method will raise a :exc:`NotImplementedError`, if the byte string
        was generated with a newer version of this library (or the byte string
        is not a valid share.)

        This method will raise a :exc:`ValueError`, if the byte string is not
        a valid share.
        """
        try:
            version = struct.unpack('>B', bytestring[:1])[0]
            if version != cls.version:
                raise NotImplementedError(
                    'unsupported version: {}'.format(version)
                )
            threshold, x = struct.unpack(
                '>BB',
                bytestring[1:3]
            )
            ys = list(struct.unpack(
                '>B' + 'B' * (len(bytestring) - 4),
                bytestring[3:]
            ))
        except struct.error as exc:
            raise ValueError('invalid share format') from exc
        return cls(threshold, x, ys)

    def __init__(self, threshold, x, ys):
        self._threshold = threshold
        self.x = x
        self._ys = ys

    @property
    def _points(self):
        return [(self.x, y) for y in self._ys]

    def _is_compatible_with(self, other):
        return (
            self.version == other.version and
            self._threshold == other._threshold and
            self.x != other.x and
            len(self._ys) == len(other._ys)
        )

    def __bytes__(self):
        return struct.pack(
            '>BBB' + 'B' * len(self._ys),
            self.version,
            self._threshold,
            self.x,
            *self._ys
        )


def split_secret(secret, threshold, share_count):
    """
    Splits up the `secret`, a byte string, into `share_count` shares from which
    the `secret` can be recovered with at least `threshold` shares.

    Returns a list of :class:`Share` objects, each representing a share.

    :param secret:
        The secret byte string to be split up.

    :param threshold:
        The number of shares shall be needed to recover the secret. This value
        must be in the range `2 <= threshold < 256`.

    :param share_count:
        The number of shares to be returned. This value must be in the range
        `threshold <= share_count < 256`.

    A :exc:`ValueError` will be raised, if `secret` is an empty string or if
    `threshold` or `share_count` has a value outside of the allowed range.
    """
    if not secret:
        raise ValueError("can't split empty secret")
    if not 2 <= threshold < 256:
        raise ValueError('threshold out of range(2, 256)')
    if not (threshold <= share_count < 256):
        raise ValueError('share_count out of range(threshold, 256)')

    shares = [Share(threshold, x, []) for x in range(1, share_count + 1)]
    for byte in secret:
        byte_shares = _split_secret_byte(byte, threshold, share_count)
        assert len(byte_shares) == share_count
        for share, (_, y) in zip(shares, byte_shares):
            share._ys.append(y)
    return shares


def _validate_shares(shares):
    if not shares:
        raise ValueError('insufficient number of shares')

    first = shares[0]
    if not all(first._is_compatible_with(share) for share in shares[1:]):
        raise ValueError('incompatible shares')
    if first._threshold > len(shares):
        raise ValueError(
            'insufficient number of shares, {} shares required'.format(
                first._threshold
            )
        )


def recover_secret(shares):
    """
    Recovers a secret from the given `shares`, provided at least as many as
    threshold shares are provided.

    If not enough shares are provided or the shares are incompatible (cannot
    possibly refer to the same secret) a :exc:`ValueError` is raised.
    """
    _validate_shares(shares)
    return bytes(
        _recover_secret_byte(byte_share)
        for byte_share in zip(*(share._points for share in shares))
    )


def add_share(shares, x):
    """
    Returns a new (or reconstructed) share for an already shared secret.

    Assuming you've split up some secret into three shares, these shares will
    be the shares `1`, `2` and `3`:

    >>> shares = split_secret(b'secret', 2, 3)
    >>> [share.x for share in shares]
    [1, 2, 3]

    You can then create a new fourth share or recreate a share you may have
    lost:

    >>> add_share(shares, 4).x
    4
    >>> add_share(shares[1:], 1).x
    1

    Take care to keep track of which shares are in circulation, to make sure
    that you're generating shares that are actually new.

    :param x:
        The share to be returned. This value must be in the range
        `1 <= x < 256`.

    If not enough shares are provided (as defined by the threshold when
    splitting the secret) or the shares are incompatible (don't refer to the
    same secret) a :exc:`ValueError` is raised.
    """
    _validate_shares(shares)
    if not (1 <= x < 256):
        raise ValueError('x not in range(1, 256)')
    return Share(
        shares[0]._threshold,
        x,
        [
            _add_share_byte(byte_share, x)
            for byte_share in zip(*(share._points for share in shares))
        ]
    )
