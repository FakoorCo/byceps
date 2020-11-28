"""
byceps.blueprints.admin.email.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import abort, request

from ....services.email import service as email_service
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_success
from ....util.framework.templating import templated
from ....util.views import redirect_to

from ...common.authorization.decorators import permission_required
from ...common.authorization.registry import permission_registry

from .authorization import EmailConfigPermission
from .forms import UpdateForm


blueprint = create_blueprint('email_admin', __name__)


permission_registry.register_enum(EmailConfigPermission)


@blueprint.route('/configs/<config_id>/update')
@permission_required(EmailConfigPermission.update)
@templated
def update_form(config_id, erroneous_form=None):
    """Show form to update an e-mail config."""
    config = _get_config_or_404(config_id)

    form = (
        erroneous_form
        if erroneous_form
        else UpdateForm(
            config_id=config.id,
            sender_address=config.sender.address,
            sender_name=config.sender.name,
            contact_address=config.contact_address,
        )
    )

    return {
        'config': config,
        'form': form,
    }


@blueprint.route('/configs/<config_id>', methods=['POST'])
@permission_required(EmailConfigPermission.update)
def update(config_id):
    """Update an e-mail config."""
    config = _get_config_or_404(config_id)

    form = UpdateForm(request.form)
    if not form.validate():
        return update_form(config.id, form)

    sender_address = form.sender_address.data.strip()
    sender_name = form.sender_name.data.strip()
    contact_address = form.contact_address.data.strip()

    config = email_service.update_config(
        config.id, sender_address, sender_name, contact_address
    )

    flash_success(f'Die E-Mail-Konfiguration wurde aktualisiert.')
    return redirect_to('brand_admin.view', brand_id=config.brand_id)


def _get_config_or_404(config_id):
    config = email_service.find_config(config_id)

    if config is None:
        abort(404)

    return config
