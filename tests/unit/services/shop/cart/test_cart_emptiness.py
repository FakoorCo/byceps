"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from decimal import Decimal

from byceps.services.shop.article.transfer.models import Article
from byceps.services.shop.cart.models import Cart


def test_is_empty_without_items():
    cart = Cart()

    assert cart.is_empty()


def test_is_empty_with_one_item():
    cart = Cart()

    add_item(cart, 1)

    assert not cart.is_empty()


def test_is_empty_with_multiple_items():
    cart = Cart()

    add_item(cart, 3)
    add_item(cart, 1)
    add_item(cart, 6)

    assert not cart.is_empty()


# helpers


def add_item(cart: Cart, quantity: int) -> None:
    article = create_article()
    cart.add_item(article, quantity)


def create_article() -> Article:
    return Article(
        id='00000000-0000-0000-0000-000000000001',
        shop_id='any-shop',
        item_number='article-123',
        description='Cool thing',
        price=Decimal('1.99'),
        tax_rate=Decimal('0.19'),
        available_from=None,
        available_until=None,
        total_quantity=1,
        quantity=1,
        max_quantity_per_order=1,
        not_directly_orderable=False,
        requires_separate_order=False,
        shipping_required=False,
    )
