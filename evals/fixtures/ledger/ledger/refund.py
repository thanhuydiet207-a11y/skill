from ledger.amounts import parse_amount


def refund_cents(amount):
    """A refund is the negated charge, in cents."""
    return -parse_amount(amount)
