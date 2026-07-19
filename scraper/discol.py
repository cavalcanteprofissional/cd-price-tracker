from scraper.nuvemshop import search_nuvemshop

BASE_URL = "https://www.discoloficial.com.br"


def search_discol(search_query: str, context=None) -> list[dict]:
    return search_nuvemshop(BASE_URL, "Discol", search_query, context)
