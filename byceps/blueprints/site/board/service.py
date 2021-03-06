"""
byceps.blueprints.site.board.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime
from typing import Dict, Optional, Sequence, Set

from flask import g

from ....services.authentication.session.models.current_user import CurrentUser
from ....services.board.models.topic import Topic as DbTopic
from ....services.board.models.posting import Posting as DbPosting
from ....services.board import (
    last_view_service as board_last_view_service,
    posting_query_service as board_posting_query_service,
)
from ....services.board.transfer.models import CategoryWithLastUpdate
from ....services.party import service as party_service
from ....services.site import settings_service as site_settings_service
from ....services.ticketing import ticket_service
from ....services.user import service as user_service
from ....services.user_badge import awarding_service as badge_awarding_service
from ....services.user_badge.transfer.models import Badge
from ....typing import BrandID, PartyID, UserID

from .models import CategoryWithLastUpdateAndUnseenFlag, Creator, Ticket


DEFAULT_POSTINGS_PER_PAGE = 10
DEFAULT_TOPICS_PER_PAGE = 10


def add_unseen_postings_flag_to_categories(
    categories: Sequence[CategoryWithLastUpdate], user: CurrentUser
) -> Sequence[CategoryWithLastUpdateAndUnseenFlag]:
    """Add flag to each category stating if it contains postings unseen
    by the user.
    """
    categories_with_flag = []

    for category in categories:
        contains_unseen_postings = (
            not user.is_anonymous
            and board_last_view_service.contains_category_unseen_postings(
                category, user.id
            )
        )

        category_with_flag = CategoryWithLastUpdateAndUnseenFlag.from_category_with_last_update(
            category, contains_unseen_postings
        )

        categories_with_flag.append(category_with_flag)

    return categories_with_flag


def add_topic_creators(topics: Sequence[DbTopic]) -> None:
    """Add each topic's creator as topic attribute."""
    creator_ids = {t.creator_id for t in topics}
    creators = user_service.find_users(creator_ids, include_avatars=True)
    creators_by_id = user_service.index_users_by_id(creators)

    for topic in topics:
        topic.creator = creators_by_id[topic.creator_id]


def add_topic_unseen_flag(topics: Sequence[DbTopic], user: CurrentUser) -> None:
    """Add `unseen` flag to topics."""
    for topic in topics:
        topic.contains_unseen_postings = (
            not user.is_anonymous
            and board_last_view_service.contains_topic_unseen_postings(
                topic, user.id
            )
        )


def add_unseen_flag_to_postings(
    postings: Sequence[DbPosting], user: CurrentUser, last_viewed_at: datetime
) -> None:
    """Add the attribute 'unseen' to each posting."""
    for posting in postings:
        posting.unseen = posting.is_unseen(user, last_viewed_at)


def enrich_creators(
    postings: Sequence[DbPosting],
    brand_id: BrandID,
    party_id: Optional[PartyID],
) -> None:
    """Enrich creators with their badges."""
    creator_ids = {posting.creator_id for posting in postings}

    badges_by_user_id = _get_badges_for_users(creator_ids, brand_id)

    if party_id is not None:
        party = party_service.get_party(party_id)
        ticket_users = ticket_service.select_ticket_users_for_party(
            creator_ids, party.id
        )
    else:
        party = None
        ticket_users = set()

    for posting in postings:
        user_id = posting.creator_id

        badges = badges_by_user_id.get(user_id, frozenset())

        if user_id in ticket_users:
            ticket = Ticket(party.title)
        else:
            ticket = None

        posting.creator = Creator.from_(posting.creator, badges, ticket)


def _get_badges_for_users(
    user_ids: Set[UserID], brand_id: BrandID
) -> Dict[UserID, Set[Badge]]:
    """Fetch users' badges that are either global or belong to the brand."""
    badges_by_user_id = badge_awarding_service.get_badges_awarded_to_users(
        user_ids, featured_only=True
    )

    def generate_items():
        for user_id, badges in badges_by_user_id.items():
            selected_badges = {
                badge for badge in badges if badge.brand_id in {None, brand_id}
            }
            yield user_id, selected_badges

    return dict(generate_items())


def calculate_posting_page_number(posting: DbPosting, user: CurrentUser) -> int:
    """Calculate the number of postings to show per page."""
    postings_per_page = get_postings_per_page_value()

    return board_posting_query_service.calculate_posting_page_number(
        posting, user, postings_per_page
    )


def get_topics_per_page_value() -> int:
    """Return the configured number of topics per page."""
    return _get_site_setting_int_value(
        'board_topics_per_page', DEFAULT_TOPICS_PER_PAGE
    )


def get_postings_per_page_value() -> int:
    """Return the configured number of postings per page."""
    return _get_site_setting_int_value(
        'board_postings_per_page', DEFAULT_POSTINGS_PER_PAGE
    )


def _get_site_setting_int_value(key, default_value) -> int:
    value = site_settings_service.find_setting_value(g.site_id, key)

    if value is None:
        return default_value

    return int(value)
