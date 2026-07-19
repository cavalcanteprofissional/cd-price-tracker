from scraper.nuvemshop import search_nuvemshop

BASE_URL = "https://www.musichousediscos.com.br"


def search_music_house(search_query: str, context=None) -> list[dict]:
    return search_nuvemshop(BASE_URL, "Music House Discos", search_query, context)
