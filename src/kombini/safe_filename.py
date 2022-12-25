from .remove_diacritic import remove_diacritics

# Characters not allowed in Linux, Windows filesystems
FORBIDDEN_CHARS = '/\\:*"?<>|'


def safe_filename(fn: str, rchar="_") -> str:
    fn = "".join(rchar if c in FORBIDDEN_CHARS else c for c in fn)
    return fn


def safe_filename_no_diacritic(fn: str) -> str:
    return safe_filename(remove_diacritics(fn.strip()))
