"""
byceps.blueprints.admin.brand.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from wtforms import StringField
from wtforms.validators import InputRequired, Length, Optional

from ....util.l10n import LocalizedForm


class _BaseForm(LocalizedForm):
    title = StringField('Titel', validators=[InputRequired(), Length(min=1, max=40)])


class CreateForm(_BaseForm):
    id = StringField('ID', validators=[InputRequired(), Length(min=1, max=20)])


class UpdateForm(_BaseForm):
    image_filename = StringField('Bild-Dateiname', validators=[Optional()])


class EmailConfigUpdateForm(LocalizedForm):
    sender_address = StringField('Absender-Adresse', validators=[InputRequired()])
    sender_name = StringField('Absender-Name', validators=[Optional()])
    contact_address = StringField('Kontaktadresse', validators=[Optional()])
