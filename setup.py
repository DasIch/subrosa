"""
    setup
    ~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import re
from pathlib import Path

from setuptools import setup

PROJECT_PATH = Path(__file__).parent.absolute()
_version_re = re.compile("__version__ = '(\d+\.\d+\.\d+)'")


def get_version():
    with (PROJECT_PATH / 'subrosa.py').open(encoding='utf-8') as f:
        for line in f:
            match = _version_re.match(line)
            if match:
                return match.group(1)
    raise ValueError('__version__ not found')


def read_text(path):
    # Python 3.4 doesn't support Path.read_text
    with path.open(encoding='utf-8') as f:
        return f.read()


if __name__ == '__main__':
    setup(
        name='subrosa',
        version=get_version(),
        description="Shamir's Secret Sharing",
        long_description=read_text(PROJECT_PATH / 'README.rst'),
        url='https://github.com/DasIch/subrosa/',
        author='Daniel Neuhäuser',
        author_email='ich@danielneuhaeuser.de',
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: Implementation :: CPython'
        ],
        py_modules=['subrosa'],
        install_requires=['gf256']
    )
