import unicodedata


def remove_diacritics(s: str) -> str:
    """
    Replace characters with diacritics with their
    vanilla equivalents
    """
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", s)
        if unicodedata.category(c) != "Mn"
    )
