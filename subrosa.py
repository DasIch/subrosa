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


class _Share:
    version = 1

    @classmethod
    def from_bytes(cls, bytestring):
        try:
            version = struct.unpack('>B', bytestring[:1])[0]
            if version != cls.version:
                raise NotImplementedError(
                    'unsupported version: {}'.format(version)
                )
            threshold, x, len_ys = struct.unpack(
                '>BBB',
                bytestring[1:4]
            )
            ys = struct.unpack('>' + 'B' * len_ys, bytestring[4:])
        except struct.error as exc:
            raise ValueError('invalid share format') from exc
        return cls(threshold, x, ys)

    def __init__(self, threshold, x, ys):
        self.threshold = threshold
        self.x = x
        self.ys = ys

    @property
    def points(self):
        return [(self.x, y) for y in self.ys]

    def is_compatible_with(self, other):
        return (
            self.version == other.version and
            self.threshold == other.threshold and
            self.x != other.x and
            len(self.ys) == len(other.ys)
        )

    def __bytes__(self):
        return struct.pack(
            '>BBBB' + 'B' * len(self.ys),
            self.version,
            self.threshold,
            self.x,
            len(self.ys),
            *self.ys
        )


def split_secret_bytes(secret, threshold, share_count):
    """
    Splits up the `secret`, a byte string, into `share_count` shares from which
    the `secret` can be recovered with at least `threshold` shares.

    Returns a list of byte strings, each representing on share. Every share is
    slightly larger than the secret (same length + some constant overhead.)

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

    shares = [_Share(threshold, x, []) for x in range(1, share_count + 1)]
    for byte in secret:
        byte_shares = _split_secret_byte(byte, threshold, share_count)
        assert len(byte_shares) == share_count
        for share, (_, y) in zip(shares, byte_shares):
            share.ys.append(y)
    return [bytes(share) for share in shares]


def recover_secret_bytes(shares):
    """
    Recovers a secret from the given `shares`, provided at least as many as
    threshold shares are provided.

    If not enough shares are provided, the shares are incompatible (cannot
    possibly refer to the same secret), or in a wrong format, a
    :exc:`ValueError` is raised.
    """
    try:
        shares = [_Share.from_bytes(share) for share in shares]
    except NotImplementedError as exc:
        raise ValueError('unsupported share format') from exc
    except ValueError as exc:
        raise ValueError('share corrupted') from exc

    if not shares:
        raise ValueError('insufficient number of shares')

    first = shares[0]
    if not all(first.is_compatible_with(share) for share in shares[1:]):
        raise ValueError('incompatible shares')
    if first.threshold > len(shares):
        raise ValueError(
            'insufficient number of shares, {} shares required'.format(
                first.threshold
            )
        )

    return bytes(
        _recover_secret_byte(byte_share)
        for byte_share in zip(*(share.points for share in shares))
    )
