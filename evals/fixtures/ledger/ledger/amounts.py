"""Money amounts are handled as integer cents."""


def parse_amount(text):
    """Parse a decimal string such as "12.34" or "-0.29" into cents."""
    return int(float(text.strip())*100)
