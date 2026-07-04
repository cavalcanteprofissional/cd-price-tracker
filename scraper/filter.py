import re
import unicodedata


def normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text


FANMADE_PATTERNS = [
    r"\bfan\s*made\b",
    r"\bfanmade\b",
    r"\bcaseir[oa]\b",
    r"\bartesanal\b",
    r"\bimpressao\s+domestica\b",
    r"\bnao\s+original\b",
    r"\bkit\s+personalizad[oa]\b",
    r"\breproducao\b",
    r"\bpersonalizad[oa]\b.{0,15}\bcd\b",
    r"\bcd\b.{0,15}\bpersonalizad[oa]\b",
    r"\bcd\s+virgem\b",
    r"\bpirata\b",
    r"\bbootleg\b",
]

_compiled = [re.compile(p) for p in FANMADE_PATTERNS]


def is_suspected_fanmade(title: str, description: str = "") -> bool:
    text = normalize(f"{title} {description}")
    return any(p.search(text) for p in _compiled)
