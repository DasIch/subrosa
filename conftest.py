"""
    conftest
    ~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os

import hypothesis


if os.environ.get('CI', 'false') == 'true':
    ENVIRONMENT = 'CI'
elif os.environ.get('TOX', 'false') == 'true':
    ENVIRONMENT = 'TOX'
else:
    ENVIRONMENT = 'DEV'


hypothesis.settings.register_profile('slow_test', {
    'DEV': hypothesis.settings(max_examples=5, timeout=-1),
    'TOX': hypothesis.settings(max_examples=10, timeout=-1),
    'CI': hypothesis.settings(timeout=-1)
}[ENVIRONMENT])


def pytest_report_header(config, startdir):
    return 'environment: {}'.format(ENVIRONMENT)
