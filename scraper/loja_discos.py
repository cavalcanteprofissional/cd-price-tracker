import logging
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.alojadediscos.com.br"
SEARCH_URL = BASE_URL + "/busca?q={}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def search_loja_discos(search_query: str, _context=None) -> list[dict]:
    logger.info("A Loja de Discos: buscando '%s'", search_query)

    items = _search_http(search_query)
    if items:
        return items

    logger.info("A Loja de Discos: search sem resultados, tentando generico")
    items = _browse_generic(search_query)
    return items


def _search_http(search_query: str) -> list[dict]:
    url = SEARCH_URL.format(quote(search_query))

    try:
        resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        if resp.status_code != 200:
            logger.warning("A Loja de Discos: search retornou %s", resp.status_code)
            return []
        return _parse_products(resp.text)
    except Exception as e:
        logger.error("A Loja de Discos: erro na busca: %s", e)
        return []


def _browse_generic(search_query: str) -> list[dict]:
    tokens = search_query.lower().split()
    if len(tokens) < 2:
        return []

    main_artist = tokens[0]
    url = f"{BASE_URL}/cd?q={quote(main_artist)}"

    try:
        resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        if resp.status_code == 200:
            return _parse_products(resp.text)
    except Exception:
        pass

    return []


def _parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    containers = soup.select("div.produto, div.product, div.item, li.product-item")
    if not containers:
        containers = soup.select("a[href*='/produto/'], a[href*='/cd/']")
        containers = [c for c in containers if c.get_text(strip=True)]

    seen = set()
    for container in containers[:30]:
        try:
            if hasattr(container, "name") and container.name == "a":
                title = container.get_text(strip=True)
                href = container.get("href", "")
                full_url = href if href.startswith("http") else BASE_URL + href
                parent_text = container.parent.get_text() if container.parent else ""
            else:
                title_el = container.select_one("h2, h3, h4, .nome-produto, .product-name")
                if not title_el:
                    a_tag = container.select_one("a[href*='/produto/'], a[href*='/cd/']")
                    if a_tag:
                        title = a_tag.get_text(strip=True)
                        href = a_tag.get("href", "")
                    else:
                        continue
                else:
                    title = title_el.get_text(strip=True)
                    a_tag = title_el.parent.select_one("a") or title_el
                    href = a_tag.get("href", "")

                full_url = href if href.startswith("http") else BASE_URL + href
                parent_text = container.get_text()

            if not title or title in seen:
                continue
            seen.add(title)

            price_match = re.search(r"por:\s*R\$\s*[\d.,]+", parent_text)
            if not price_match:
                price_match = re.search(r"R\$\s*[\d.,]+", parent_text)
            price_text = price_match.group(0) if price_match else ""

            items.append({
                "title": title.strip(),
                "price_text": price_text,
                "seller_name": None,
                "listing_url": full_url,
            })
        except Exception as e:
            logger.debug("A Loja de Discos: erro ao extrair item: %s", e)
            continue

    if items:
        for item in items[:3]:
            logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])

    return items
