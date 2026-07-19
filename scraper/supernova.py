from scraper.nuvemshop import search_nuvemshop

BASE_URL = "https://www.supernovadiscos.com.br"


def search_supernova(search_query: str, context=None) -> list[dict]:
    return search_nuvemshop(BASE_URL, "Supernova Discos", search_query, context)
