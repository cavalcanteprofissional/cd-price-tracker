import re


def parse_br_price(text: str) -> float:
    text = text.strip()
    text = re.sub(r"[R$\s]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return float(text)
