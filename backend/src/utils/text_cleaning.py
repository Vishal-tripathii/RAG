import re

#   is a non-breaking space, which pdfplumber emits fairly often; \f turns up
# as a page-break marker. Both are horizontal whitespace for our purposes.
_HORIZONTAL_WS = re.compile(r"[ \t\f\v ]+")
_SPACE_BEFORE_NEWLINE = re.compile(r" +\n")
_BLANK_LINE_RUNS = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    # Collapses runs of spaces and tabs but deliberately keeps newlines. This
    # used to be a single re.sub(r"\s+", " ") - and since \s matches \n, it left
    # the text with no line breaks at all. The chunker's separator list is
    # ["\n\n", "\n", " ", ""], so the first two could never match and recursive
    # splitting silently degraded to fixed-width slicing on spaces, cutting
    # chunks mid-sentence regardless of the document's structure.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HORIZONTAL_WS.sub(" ", text)
    text = _SPACE_BEFORE_NEWLINE.sub("\n", text)
    text = _BLANK_LINE_RUNS.sub("\n\n", text)
    return text.strip()
