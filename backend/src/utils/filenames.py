import re

_INVALID_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')


def sanitize_filename(filename: str) -> str:
    return _INVALID_CHARS.sub("_", filename).strip(" .")
