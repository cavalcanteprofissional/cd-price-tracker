import logging
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from scraper.utils import normalize, token_similarity, best_match

logger = logging.getLogger(__name__)

BASE_URL = "https://www.migranet.com.br"
SEARCH_URL = BASE_URL + "/buscar?q={}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def search_migranet(search_query: str, _context=None) -> list[dict]:
    logger.info("Migranet: buscando '%s'", search_query)

    url = SEARCH_URL.format(quote(search_query))
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Migranet: erro HTTP %s", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.select("div.listagem-item")

    if not containers:
        logger.warning("Migranet: nenhum produto encontrado")
        return []

    logger.info("Migranet: %d produtos encontrados", len(containers))

    items = []
    for container in containers[:20]:
        try:
            title_el = container.select_one("a.nome-produto")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            href = title_el.get("href", "")
            full_url = href if href.startswith("http") else BASE_URL + href

            price_el = container.select_one("strong.preco-promocional")
            price_text = ""
            if price_el:
                data_price = price_el.get("data-sell-price")
                if data_price:
                    price_text = f"R$ {data_price}"
                else:
                    price_text = price_el.get_text(strip=True)

            items.append({
                "title": title,
                "price_text": price_text,
                "seller_name": None,
                "listing_url": full_url,
            })
        except Exception as e:
            logger.debug("Migranet: erro ao extrair item: %s", e)
            continue

    if items:
        for item in items[:3]:
            logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])

    return items
