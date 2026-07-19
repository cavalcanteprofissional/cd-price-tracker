import logging
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from scraper.utils import normalize, token_similarity, best_match

logger = logging.getLogger(__name__)

BASE_URL = "https://www.locomotivadiscos.com.br"
SEARCH_URL = BASE_URL + "/search.html?searchQuery={}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def search_locomotiva(search_query: str, _context=None) -> list[dict]:
    logger.info("Locomotiva: buscando '%s'", search_query)

    url = SEARCH_URL.format(quote(search_query))

    try:
        resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Locomotiva: erro HTTP %s", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.select("div.product-item-container")

    if not containers:
        logger.warning("Locomotiva: nenhum produto encontrado na pagina")
        return []

    logger.info("Locomotiva: %d produtos encontrados", len(containers))

    items = []
    for container in containers[:20]:
        try:
            title_el = container.select_one(".iluria-layout-search-product-title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            href = title_el.get("href", "")
            full_url = BASE_URL + "/" + href.lstrip("/") if href else ""

            currency_el = container.select_one(".product-price-currency")
            price_el = container.select_one(".product-price-text")
            price_text = None
            if currency_el and price_el:
                price_text = (currency_el.get_text(strip=True) + price_el.get_text(strip=True)).strip()

            items.append({
                "title": title,
                "price_text": price_text,
                "seller_name": None,
                "listing_url": full_url,
            })
        except Exception as e:
            logger.debug("Locomotiva: erro ao extrair item: %s", e)
            continue

    if items:
        for item in items[:3]:
            logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])

    return items
