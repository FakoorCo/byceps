"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import pytest

from byceps.util.iterables import find


@pytest.mark.parametrize(
    'iterable, predicate, expected',
    [
        (
            [],
            lambda x: x > 3,
            None,
        ),
        (
            [-2, 0, 1, 3],
            lambda x: x > 3,
            None,
        ),
        (
            [2, 3, 4, 5],
            lambda x: x > 3,
            4,
        ),
    ],
)
def test_find(iterable, predicate, expected):
    actual = find(iterable, predicate)
    assert actual == expected
