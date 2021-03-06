"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.shop.order import (
    sequence_service as order_sequence_service,
)
from byceps.services.shop.shop import service as shop_service

from tests.integration.services.shop.helpers import create_shop


@pytest.fixture(scope='module')
def shop1(make_brand):
    brand = make_brand()
    shop = create_shop(brand.id)
    yield shop
    shop_service.delete_shop(shop.id)


@pytest.fixture(scope='module')
def shop2(make_brand):
    brand = make_brand()
    shop = create_shop(brand.id)
    yield shop
    shop_service.delete_shop(shop.id)


def test_generate_order_number_default(admin_app, shop1):
    shop = shop1

    order_number_sequence_id = (
        order_sequence_service.create_order_number_sequence(shop.id, 'AEC-01-B')
    )

    actual = order_sequence_service.generate_order_number(
        order_number_sequence_id
    )

    assert actual == 'AEC-01-B00001'

    order_sequence_service.delete_order_number_sequence(
        order_number_sequence_id
    )


def test_generate_order_number_custom(admin_app, shop2):
    shop = shop2

    last_assigned_order_sequence_number = 206

    order_number_sequence_id = (
        order_sequence_service.create_order_number_sequence(
            shop.id, 'LOL-03-B', value=last_assigned_order_sequence_number
        )
    )

    actual = order_sequence_service.generate_order_number(
        order_number_sequence_id
    )

    assert actual == 'LOL-03-B00207'

    order_sequence_service.delete_order_number_sequence(
        order_number_sequence_id
    )
