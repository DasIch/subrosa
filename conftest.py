"""
    conftest
    ~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os

import pytest


RUNNING_ON_CI = os.environ.get('CI', 'false') == 'true'


def pytest_addoption(parser):
    parser.addoption(
        '--all', action='store_true', default=False,
        help='Run all tests'
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'ci_only: mark test to only run in CI'
    )


def pytest_runtest_setup(item):
    slow_marker = item.get_marker('ci_only')
    run_all_tests = item.config.getoption('--all')
    if slow_marker is not None and not (RUNNING_ON_CI or run_all_tests):
        pytest.skip('ci_only test skipped during local testing')
