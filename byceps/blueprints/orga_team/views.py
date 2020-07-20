"""
byceps.blueprints.orga_team.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import dataclasses
from dataclasses import dataclass

from flask import abort, g

from ...services.orga_team import service as orga_team_service
from ...services.user import service as user_service
from ...services.user.transfer.models import User
from ...util.framework.blueprint import create_blueprint
from ...util.framework.templating import templated


@dataclass(frozen=True)
class Orga:
    user: User
    full_name: str
    team_name: str
    duties: str


blueprint = create_blueprint('orga_team', __name__)


@blueprint.route('/')
@templated
def index():
    """List all organizers for the current party."""
    if g.party_id is None:
        # No party is configured for the current site.
        abort(404)

    memberships = orga_team_service.get_memberships_for_party(g.party_id)

    users_by_id = _get_users_by_id(memberships)

    def _to_orga(membership):
        user = users_by_id[membership.user_id]

        return Orga(
            user,
            membership.user.detail.full_name,
            membership.orga_team.title,
            membership.duties,
        )

    orgas = list(map(_to_orga, memberships))
    orgas.sort(key=lambda orga: user_service.get_sort_key_for_screen_name(orga.user))

    return {
        'orgas': orgas,
    }


def _get_users_by_id(memberships):
    user_ids = {ms.user_id for ms in memberships}

    users = user_service.find_users(user_ids, include_avatars=True)

    # Each of these users is an organizer.
    users = {dataclasses.replace(u, is_orga=True) for u in users}

    return {user.id: user for user in users}
