import re

JUNK_PATTERNS = [
    re.compile(r"arxiv:\d{4}\.\d{4,5}(v\d+)?\s*\[[\w\.]+\]", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*$", re.MULTILINE),
    re.compile(r"^\s*(figure|fig|table)\s*\d+[:\.].*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(\$[^$]+\$|\\\w+\{[^}]*\}|\\[a-zA-Z]+)", re.IGNORECASE),
    re.compile(r"\[\d+\](\s*\w+,.*?\(\d{4}\)\.?)+", re.DOTALL),
]

CROSSREF_PATTERNS = [
    re.compile(r"as shown in (table|figure|fig\.?)\s*\d+,?\s*", re.IGNORECASE),
    re.compile(r"see (table|figure|fig\.?)\s*\d+,?\s*", re.IGNORECASE),
    re.compile(r"as reported in section\s*\d+(\.\d+)*,?\s*", re.IGNORECASE),
    re.compile(r"cf\.?\s*(figure|table)\s*\d+,?\s*", re.IGNORECASE),
    re.compile(r"in (table|figure|fig\.?)\s*\d+,?\s*", re.IGNORECASE),
]


def is_junk(text: str) -> bool:
    stripped = text.strip()
    if len(stripped.split()) < 8:
        return True
    for pattern in JUNK_PATTERNS:
        if pattern.search(stripped):
            return True
    return False


def strip_crossrefs(text: str) -> str:
    for pattern in CROSSREF_PATTERNS:
        text = pattern.sub("", text)
    return text


def clean_text(text: str) -> str:
    text = strip_crossrefs(text)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if not is_junk(line):
            cleaned.append(line)
    return "\n".join(cleaned).strip()
