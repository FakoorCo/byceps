"""
byceps.blueprints.admin.ticketing.checkin.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import date

from flask import abort, request

from .....services.party import service as party_service
from .....services.ticketing import ticket_service
from .....util.framework.blueprint import create_blueprint
from .....util.framework.templating import templated

from ....common.authorization.decorators import permission_required

from ...ticketing.authorization import TicketingPermission
from ...user import service as user_blueprint_service


blueprint = create_blueprint('ticketing_checkin', __name__)


MINIMUM_AGE_IN_YEARS = 18


@blueprint.route('/for_party/<party_id>')
@permission_required(TicketingPermission.checkin)
@templated
def index(party_id):
    """Provide form to find tickets, then check them in."""
    party = party_service.find_party(party_id)
    if party is None:
        abort(404)

    search_term = request.args.get('search_term', default='').strip()

    limit = 10

    if search_term:
        latest_dob_for_checkin = _get_latest_date_of_birth_for_checkin()
        tickets = _search_tickets(party.id, search_term, limit)
        users = _search_users(search_term, limit)

        tickets += list(_get_tickets_for_users(party.id, users))
    else:
        latest_dob_for_checkin = None
        tickets = None
        users = None

    return {
        'party': party,
        'latest_dob_for_checkin': latest_dob_for_checkin,
        'search_term': search_term,
        'tickets': tickets,
        'users': users,
    }


def _get_latest_date_of_birth_for_checkin():
    today = date.today()
    return today.replace(year=today.year - MINIMUM_AGE_IN_YEARS)


def _search_tickets(party_id, search_term, limit):
    page = 1
    per_page = limit

    tickets_pagination = ticket_service.get_tickets_with_details_for_party_paginated(
        party_id, page, per_page, search_term=search_term
    )

    return tickets_pagination.items


def _search_users(search_term, limit):
    page = 1
    per_page = limit

    users_pagination = user_blueprint_service.get_users_paginated(
        page, per_page, search_term=search_term
    )

    # Exclude deleted users.
    users_pagination.items = [
        user for user in users_pagination.items if not user.deleted
    ]

    return users_pagination.items


def _get_tickets_for_users(party_id, users):
    for user in users:
        yield from ticket_service.find_tickets_related_to_user_for_party(
            user.id, party_id
        )
