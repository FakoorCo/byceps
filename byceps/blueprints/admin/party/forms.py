"""
byceps.blueprints.admin.party.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from wtforms import BooleanField, DateTimeField, IntegerField, StringField
from wtforms.validators import InputRequired, Length, Optional

from ....util.l10n import LocalizedForm


class _BaseForm(LocalizedForm):
    title = StringField('Titel', validators=[Length(min=1, max=40)])
    starts_at = DateTimeField('Beginn', format='%d.%m.%Y %H:%M', validators=[InputRequired()])
    ends_at = DateTimeField('Ende', format='%d.%m.%Y %H:%M', validators=[InputRequired()])
    max_ticket_quantity = IntegerField('Maximale Anzahl Tickets', validators=[Optional()])


class CreateForm(_BaseForm):
    id = StringField('ID', validators=[Length(min=1, max=40)])


class UpdateForm(_BaseForm):
    ticket_management_enabled = BooleanField('Ticketverwaltung geöffnet')
    seat_management_enabled = BooleanField('Sitzplatzverwaltung geöffnet')
    canceled = BooleanField('abgesagt')
    archived = BooleanField('archiviert')
