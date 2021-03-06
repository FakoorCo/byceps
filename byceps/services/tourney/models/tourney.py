"""
byceps.services.tourney.models.tourney
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime

from ....database import db, generate_uuid

from ....util.instances import ReprBuilder

from .tourney_category import TourneyCategory


class Tourney(db.Model):
    """A tournament."""

    __tablename__ = 'tourneys'
    __table_args__ = (
        db.UniqueConstraint('category_id', 'title'),
    )

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    category_id = db.Column(
        db.Uuid,
        db.ForeignKey('tourney_categories.id'),
        index=True,
        nullable=False,
    )
    category = db.relationship(TourneyCategory)
    title = db.Column(db.UnicodeText, nullable=False)
    subtitle = db.Column(db.UnicodeText, nullable=True)
    logo_url = db.Column(db.UnicodeText, nullable=True)
    max_participant_count = db.Column(db.Integer, nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, category: TourneyCategory, title: str, max_participant_count: bool, starts_at: datetime) -> None:
        self.category = category
        self.title = title
        self.max_participant_count = max_participant_count
        self.starts_at = starts_at

    def __repr__(self) -> str:
        return ReprBuilder(self) \
            .add_with_lookup('title') \
            .build()
