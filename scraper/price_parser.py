import re


def parse_br_price(text: str) -> float:
    text = text.strip()
    text = re.sub(r"[R$\s]", "", text)
    # Remove duplicatas de separadores: "374..02" ou "374,,02"
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r",{2,}", ",", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    # Remove pontos extras no final: "374." -> "374"
    text = text.rstrip(".")
    if not text:
        return 0.0
    return float(text)
