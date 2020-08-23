"""
byceps.blueprints.site.seating.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import abort, g, request

from ....services.party import service as party_service
from ....services.seating import area_service as seating_area_service
from ....services.seating.models.seat import Seat
from ....services.seating import seat_service
from ....services.seating.transfer.models import SeatID
from ....services.ticketing.models.ticket import Ticket as DbTicket
from ....services.ticketing import (
    exceptions as ticket_exceptions,
    ticket_seat_management_service,
    ticket_service,
)
from ....services.ticketing.transfer.models import TicketID
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_error, flash_success
from ....util.framework.templating import templated
from ....util.views import respond_no_content

from ...admin.seating.authorization import SeatingPermission
from ...common.authentication.decorators import login_required
from ...common.authorization.registry import permission_registry

from . import service


blueprint = create_blueprint('seating', __name__)


permission_registry.register_enum(SeatingPermission)


@blueprint.route('/')
@templated
def index():
    """List areas."""
    if g.party_id is None:
        # No party is configured for the current site.
        abort(404)

    areas = seating_area_service.get_areas_for_party(g.party_id)

    return {
        'areas': areas,
    }


@blueprint.route('/areas/<slug>')
@templated
def view_area(slug):
    """View area."""
    if g.party_id is None:
        # No party is configured for the current site.
        abort(404)

    area = seating_area_service.find_area_for_party_by_slug(g.party_id, slug)
    if area is None:
        abort(404)

    seat_management_enabled = _is_seat_management_enabled()

    seats = seat_service.get_seats_with_tickets_for_area(area.id)

    users_by_id = service.get_users(seats, [])

    seats = service.get_seats(seats, users_by_id)

    return {
        'area': area,
        'seat_management_enabled': seat_management_enabled,
        'seats': seats,
        'manage_mode': False,
    }


@blueprint.route('/areas/<slug>/manage_seats')
@login_required
@templated('site/seating/view_area')
def manage_seats_in_area(slug):
    """Manage seats for assigned tickets in area."""
    _abort_if_seat_management_disabled()

    area = seating_area_service.find_area_for_party_by_slug(g.party_id, slug)
    if area is None:
        abort(404)

    seat_management_enabled = _is_seat_management_enabled()

    seats = seat_service.get_seats_with_tickets_for_area(area.id)

    ticket_code = request.args.get('ticket_code')
    selected_ticket_id = request.args.get('ticket_id')

    if _is_seating_admin(g.current_user) and ticket_code:
        ticket_code = ticket_code.upper()
        ticket = ticket_service.find_ticket_by_code(ticket_code)
        if ticket:
            tickets = ticket_service.find_tickets_for_seat_manager(
                ticket.get_seat_manager().id, g.party_id
            )
            selected_ticket_id = ticket.id
        else:
            flash_error(f'Ticket code "{ticket_code}" not found.')
            tickets = []
            selected_ticket_id = None

    elif _is_seating_admin(g.current_user) and selected_ticket_id:
        ticket = ticket_service.find_ticket(selected_ticket_id)
        if ticket:
            tickets = ticket_service.find_tickets_for_seat_manager(
                ticket.get_seat_manager().id, g.party_id
            )
            selected_ticket_id = ticket.id
        else:
            flash_error(f'Ticket ID "{selected_ticket_id}" not found.')
            tickets = []
            selected_ticket_id = None

    elif seat_management_enabled:
        tickets = ticket_service.find_tickets_for_seat_manager(
            g.current_user.id, g.party_id
        )
        selected_ticket_id = None

    else:
        tickets = []
        selected_ticket_id = None

    users_by_id = service.get_users(seats, tickets)

    seats = service.get_seats(seats, users_by_id)

    if seat_management_enabled:
        managed_tickets = list(
            service.get_managed_tickets(tickets, users_by_id)
        )
    else:
        managed_tickets = []

    return {
        'area': area,
        'seat_management_enabled': seat_management_enabled,
        'seats': seats,
        'manage_mode': True,
        'managed_tickets': managed_tickets,
        'selected_ticket_id': selected_ticket_id,
    }


def _get_users(seats, managed_tickets):
    return {}  # Not implemented.


@blueprint.route(
    '/ticket/<uuid:ticket_id>/seat/<uuid:seat_id>', methods=['POST']
)
@login_required
@respond_no_content
def occupy_seat(ticket_id, seat_id):
    """Use ticket to occupy seat."""
    _abort_if_seat_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user

    if not ticket.is_seat_managed_by(manager.id) and not _is_seating_admin(
        manager
    ):
        flash_error(
            'Du bist nicht berechtigt, den Sitzplatz '
            f'für Ticket {ticket.code} zu verwalten.'
        )
        return

    seat = _get_seat_or_404(seat_id)

    if seat.is_occupied:
        flash_error(f'{seat.label} ist bereits belegt.')
        return

    try:
        ticket_seat_management_service.occupy_seat(
            ticket.id, seat.id, manager.id
        )
    except ticket_exceptions.SeatChangeDeniedForBundledTicket:
        flash_error(
            f'Ticket {ticket.code} gehört zu einem Paket '
            'und kann nicht einzeln verwaltet werden.'
        )
        return
    except ticket_exceptions.TicketCategoryMismatch:
        flash_error(
            f'Ticket {ticket.code} und {seat.label} haben '
            'unterschiedliche Kategorien.'
        )
        return
    except ValueError:
        abort(404)

    flash_success(f'{seat.label} wurde mit Ticket {ticket.code} reserviert.')


@blueprint.route('/ticket/<uuid:ticket_id>/seat', methods=['DELETE'])
@login_required
@respond_no_content
def release_seat(ticket_id):
    """Release the seat."""
    _abort_if_seat_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    if not ticket.occupied_seat:
        flash_error(f'Ticket {ticket.code} belegt keinen Sitzplatz.')
        return

    manager = g.current_user

    if not ticket.is_seat_managed_by(manager.id) and not _is_seating_admin(
        manager
    ):
        flash_error(
            'Du bist nicht berechtigt, den Sitzplatz '
            f'für Ticket {ticket.code} zu verwalten.'
        )
        return

    seat = ticket.occupied_seat

    try:
        ticket_seat_management_service.release_seat(ticket.id, manager.id)
    except ticket_exceptions.SeatChangeDeniedForBundledTicket:
        flash_error(
            f'Ticket {ticket.code} gehört zu einem Paket '
            'und kann nicht einzeln verwaltet werden.'
        )
        return

    flash_success(f'{seat.label} wurde freigegeben.')


def _abort_if_seat_management_disabled() -> None:
    if not _is_seat_management_enabled():
        flash_error('Sitzplätze können derzeit nicht verändert werden.')
        return


def _is_seat_management_enabled():
    if g.current_user.is_anonymous:
        return False

    if g.party_id is None:
        return False

    if _is_seating_admin(g.current_user):
        return True

    party = party_service.get_party(g.party_id)
    return party.seat_management_enabled


def _is_seating_admin(user) -> bool:
    return user.has_permission(SeatingPermission.administrate)


def _get_ticket_or_404(ticket_id: TicketID) -> DbTicket:
    ticket = ticket_service.find_ticket(ticket_id)

    if (ticket is None) or ticket.revoked:
        abort(404)

    return ticket


def _get_seat_or_404(seat_id: SeatID) -> Seat:
    seat = seat_service.find_seat(seat_id)

    if seat is None:
        abort(404)

    return seat