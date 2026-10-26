def slugify(title):
    """Lowercase a title and join its words with dashes."""
    return title.strip().lower().replace(' ', '_')
