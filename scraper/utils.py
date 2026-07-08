import re
import unicodedata


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s]", "", text)


def token_similarity(a: str, b: str) -> float:
    a_tokens = set(normalize(a).split())
    b_tokens = set(normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    return len(intersection) / max(len(a_tokens), len(b_tokens))


def first_selector(parent, selectors: list[str]):
    for sel in selectors:
        el = parent.query_selector(sel)
        if el:
            return el
    return None


def best_match(candidates: list[dict], expected: str, artist: str) -> dict | None:
    if not candidates:
        return None
    artist_tokens = set(normalize(artist).split())

    def score(c):
        s = token_similarity(expected, c["title"])
        if s <= 0 and artist_tokens:
            info_norm = normalize(c.get("_info", ""))
            if any(t in info_norm for t in artist_tokens):
                s = 0.15
        return s

    best = max(candidates, key=score)
    best_score = score(best)
    return best if best_score >= 0.15 else None
