# -*- coding: utf-8 -*-

"""
byceps.blueprints.shop.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from datetime import datetime
from enum import Enum

from flask import g
from Ranger import Range
from Ranger.src.Range.Cut import Cut
from sqlalchemy.ext.hybrid import hybrid_property

from ...database import BaseQuery, db, generate_uuid
from ...util.instances import ReprBuilder
from ...util.money import EuroAmount

from ..party.models import Party
from ..user.models import User


class ArticleQuery(BaseQuery):

    def for_current_party(self):
        return self.for_party(g.party)

    def for_party(self, party):
        return self.filter_by(party_id=party.id)


class Article(db.Model):
    """An article that can be bought."""
    __tablename__ = 'shop_articles'
    __table_args__ = (
        db.UniqueConstraint('party_id', 'description'),
    )
    query_class = ArticleQuery

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    party_id = db.Column(db.Unicode(20), db.ForeignKey('parties.id'), index=True, nullable=False)
    party = db.relationship(Party)
    description = db.Column(db.Unicode(80), nullable=False)
    _price = db.Column('price', db.Integer, nullable=False)
    available_from = db.Column(db.DateTime, nullable=True)
    available_until = db.Column(db.DateTime, nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    max_quantity_per_order = db.Column(db.Integer, nullable=True)
    requires_separate_order = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, party, description, price, quantity,
                 *, available_from=None, available_until=None):
        self.party = party
        self.description = description
        self._price = price.to_int()
        self.available_from = available_from
        self.available_until = available_until
        self.quantity = quantity

    @hybrid_property
    def price(self):
        return EuroAmount.from_int(int(self._price))

    @price.setter
    def price(self, amount):
        self._price = amount.to_int()

    @property
    def availability_range(self):
        """Assemble the date/time range of the articles availability."""
        start = self.available_from
        end = self.available_until

        if start:
            if end:
                return Range.closedOpen(start, end)
            else:
                return Range.atLeast(start)
        else:
            if end:
                return Range.lessThan(end)
            else:
                return range_all(datetime)

    @property
    def is_available(self):
        """Return `True` if the article is available at this moment in time."""
        now = datetime.now()
        return self.availability_range.contains(now)

    def __repr__(self):
        return ReprBuilder(self) \
            .add_with_lookup('id') \
            .add('party', self.party_id) \
            .add_with_lookup('description') \
            .add_with_lookup('quantity') \
            .build()


def range_all(theType):
    """Create a range than contains every value of the given type."""
    return Range(
        Cut.belowAll(theType=theType),
        Cut.aboveAll(theType=theType))


PaymentState = Enum('PaymentState', ['open', 'canceled', 'paid'])


class OrderQuery(BaseQuery):

    def for_current_party(self):
        return self.for_party(g.party)

    def for_party(self, party):
        return self.filter_by(party_id=party.id)


class Order(db.Model):
    """An order for articles, placed by a user."""
    __tablename__ = 'shop_orders'
    query_class = OrderQuery

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    party_id = db.Column(db.Unicode(20), db.ForeignKey('parties.id'), index=True, nullable=False)
    party = db.relationship(Party)
    placed_by_id = db.Column(db.Uuid, db.ForeignKey('users.id'), index=True, nullable=False)
    placed_by = db.relationship(User, foreign_keys=[placed_by_id])
    first_names = db.Column(db.Unicode(40), nullable=False)
    last_name = db.Column(db.Unicode(40), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    zip_code = db.Column(db.Unicode(5), nullable=False)
    city = db.Column(db.Unicode(40), nullable=False)
    street = db.Column(db.Unicode(40), nullable=False)
    _payment_state = db.Column('payment_state', db.Unicode(20), nullable=False)
    payment_state_updated_at = db.Column(db.DateTime)
    payment_state_updated_by_id = db.Column(db.Uuid, db.ForeignKey('users.id'))
    payment_state_updated_by = db.relationship(User, foreign_keys=[payment_state_updated_by_id])

    def __init__(self, party, placed_by, first_names, last_name, date_of_birth,
                 zip_code, city, street):
        self.party = party
        self.placed_by = placed_by
        self.first_names = first_names
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.zip_code = zip_code
        self.city = city
        self.street = street
        self.payment_state = PaymentState.open

    @hybrid_property
    def payment_state(self):
        return PaymentState[self._payment_state]

    @payment_state.setter
    def payment_state(self, state):
        assert state is not None
        self._payment_state = state.name

    def add_item(self, article, quantity):
        """Add an article as an item to this order.

        Return the resulting order item so it can be added to the
        database session.
        """
        return OrderItem(self, article, quantity=quantity)

    def cancel(self):
        """Cancel the order."""
        self._update_payment_state(PaymentState.canceled)

    def mark_as_paid(self):
        """Mark the order as being paid for."""
        self._update_payment_state(PaymentState.paid)

    def _update_payment_state(self, state):
        self.payment_state = state
        self.payment_state_updated_at = datetime.now()
        self.payment_state_updated_by = g.current_user

    def collect_articles(self):
        """Return the articles associated with this order."""
        return {item.article for item in self.items}

    def __repr__(self):
        return ReprBuilder(self) \
            .add_with_lookup('id') \
            .add('party', self.party_id) \
            .add('placed_by', self.placed_by.screen_name) \
            .add_custom('{:d} items'.format(len(self.items))) \
            .add_custom(self.payment_state.name) \
            .build()


class OrderItem(db.Model):
    """An item that belongs to an order."""
    __tablename__ = 'shop_order_items'

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    order_id = db.Column(db.Uuid, db.ForeignKey('shop_orders.id'), index=True, nullable=False)
    order = db.relationship(Order, backref='items')
    article_id = db.Column(db.Uuid, db.ForeignKey('shop_articles.id'), index=True, nullable=False)
    article = db.relationship(Article)
    description = db.Column(db.Unicode(80), nullable=False)
    _price = db.Column('price', db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __init__(self, order, article, quantity):
        self.order = order
        self.article = article
        self.description = article.description
        self.price = article.price
        self.quantity = quantity

    @hybrid_property
    def price(self):
        return EuroAmount.from_int(self._price)

    @price.setter
    def price(self, amount):
        self._price = amount.to_int()
