"""
byceps.services.tourney.transfer.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import NewType, Optional
from uuid import UUID

from ....typing import PartyID

from ...user.transfer.models import User


TourneyCategoryID = NewType('TourneyCategoryID', UUID)


@dataclass(frozen=True)
class TourneyCategory:
    id: TourneyCategoryID
    party_id: PartyID
    position: int
    title: str


TourneyID = NewType('TourneyID', UUID)


@dataclass(frozen=True)
class Tourney:
    id: TourneyID
    category_id: TourneyCategoryID
    title: str
    subtitle: str
    current_participant_count: int
    max_participant_count: int


MatchID = NewType('MatchID', UUID)


MatchCommentID = NewType('MatchCommentID', UUID)


ParticipantID = NewType('ParticipantID', UUID)


@dataclass(frozen=True)
class Match:
    id: MatchID


@dataclass(frozen=True)
class MatchComment:
    id: MatchCommentID
    match_id: MatchID
    created_at: datetime
    created_by: User
    body_text: str
    body_html: str
    last_edited_at: Optional[datetime]
    last_edited_by: Optional[User]
    hidden: bool
    hidden_at: Optional[datetime]
    hidden_by: Optional[User]
