from ledger.amounts import parse_amount


def invoice_total(lines):
    """Sum invoice line amounts given as decimal strings; returns cents."""
    return sum(parse_amount(line) for line in lines)
