Subrosa Documentation
=====================

Subrosa is an implementation of `Shamir's Secret Sharing`__.

__ https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing


Tutorial
--------

You can split the secret using :func:`split_secret` into shares. For this you
need the secret as a byte string, you need the number of shares you want and
the threshold - how many shares should be necessary to recover the secret.

For this example the secret will be the byte string `b'supersecretpassword'`,
we will create three shares and two of them should be required to recover the
secret.

>>> shares = split_secret(b'supersecretpassword', 2, 3)

`split_secret` returns a list of :class:`Share` objects. We can store these
objects in a file or a database as a byte string, which we create using the
:func:`bytes` function.

>>> binary_shares = [bytes(share) for share in shares]

The byte strings have roughly the same length as the secret. They're also
versioned, so that the format can be changed in the future but old shares can
still be easily supported by future versions.

If you're retrieving these shares as byte strings, you can turn them back into
objects using :meth:`Share.from_bytes`.

>>> shares = [Share.from_bytes(share) for share in binary_shares]

To recover the secret simply pass at least as many shares to
:func:`recover_secret` as you've defined should be required for this, when
splitting the secret.

>>> recover_secret(shares[:2])
b'supersecretpassword'


API Reference
-------------

.. module:: subrosa

.. autofunction:: split_secret

.. autofunction:: recover_secret

.. autofunction:: add_share

.. autoclass:: Share
   :members:


Additional Information
----------------------

.. toctree::

   license
