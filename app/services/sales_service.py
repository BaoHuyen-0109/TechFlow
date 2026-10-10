"""Sales module public service interface."""
from app.services.transaction_service import create_document, transition


def create_order(actor_id, header, lines, code=None):
    return create_document('sales', actor_id, header, lines, code)


def complete_order(actor_id, identifier):
    return transition('sales', actor_id, identifier, 'complete')


def cancel_order(actor_id, identifier):
    return transition('sales', actor_id, identifier, 'cancel')
