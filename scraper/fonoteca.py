from scraper.nuvemshop import search_nuvemshop

BASE_URL = "https://www.fonoteca.com.br"


def search_fonoteca(search_query: str, context=None) -> list[dict]:
    return search_nuvemshop(BASE_URL, "Fonoteca", search_query, context)
