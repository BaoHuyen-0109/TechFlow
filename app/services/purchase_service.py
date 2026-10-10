"""Purchase module public service interface."""
from app.services.transaction_service import create_document, transition


def create_receipt(actor_id, header, lines, code=None):
    return create_document('purchases', actor_id, header, lines, code)


def complete_receipt(actor_id, identifier):
    return transition('purchases', actor_id, identifier, 'complete')


def cancel_receipt(actor_id, identifier):
    return transition('purchases', actor_id, identifier, 'cancel')
