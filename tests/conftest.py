"""
:Copyright: 2006-2019 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from contextlib import contextmanager

import pytest

from byceps.database import db as _db

from tests.base import CONFIG_FILENAME_TEST_ADMIN, \
    CONFIG_FILENAME_TEST_PARTY, create_app
from tests.helpers import create_user


@pytest.fixture(scope='session')
def db():
    return _db


@contextmanager
def database_recreated(db):
    db.reflect()
    db.drop_all()

    db.create_all()

    yield


@pytest.fixture(scope='session')
def admin_app():
    """Provide the admin web application."""
    app = create_app(CONFIG_FILENAME_TEST_ADMIN)
    yield app


@pytest.fixture
def admin_app_with_db(admin_app, db):
    with admin_app.app_context():
        with database_recreated(db):
            yield admin_app
        db.session.remove()


@pytest.fixture
def admin_client(admin_app):
    """Provide a test HTTP client against the admin web application."""
    return admin_app.test_client()


@pytest.fixture(scope='session')
def party_app():
    """Provide a party web application."""
    app = create_app(CONFIG_FILENAME_TEST_PARTY)
    yield app


@pytest.fixture
def party_app_with_db(party_app, db):
    with party_app.app_context():
        with database_recreated(db):
            yield party_app
        db.session.remove()


@pytest.fixture
def admin_user():
    return create_user('Admin')


@pytest.fixture
def normal_user():
    return create_user()