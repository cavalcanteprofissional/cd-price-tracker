import json
import logging
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from scraper.utils import normalize

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def search_nuvemshop(base_url: str, name: str, search_query: str, _context=None) -> list[dict]:
    logger.info("%s: buscando '%s'", name, search_query)

    url = f"{base_url}/produtos/?q={quote(search_query)}"
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.error("%s: erro HTTP %s", name, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    items = _extract_from_html(soup, base_url)

    if not items:
        logger.warning("%s: nenhum resultado na pagina 1, tentando pagina 2", name)
        url2 = f"{base_url}/produtos/page/2/?q={quote(search_query)}"
        try:
            resp2 = httpx.get(url2, headers=HEADERS, timeout=30, follow_redirects=True)
            if resp2.status_code == 200:
                soup2 = BeautifulSoup(resp2.text, "html.parser")
                items = _extract_from_html(soup2, base_url)
        except Exception:
            pass

    if items:
        query_tokens = set(normalize(search_query).split())
        matching = [i for i in items if query_tokens & set(normalize(i["title"]).split())]
        if not matching:
            logger.warning("%s: busca retornou %d produtos mas nenhum contem termos da query '%s' — provavel fallback do catalogo", name, len(items), search_query)
            return []
        logger.info("%s: %d candidatos extraidos (%d com match na query)", name, len(items), len(matching))
        for item in matching[:3]:
            logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])
    else:
        logger.warning("%s: nenhum candidato encontrado", name)

    return items


def _extract_from_html(soup: BeautifulSoup, base_url: str) -> list[dict]:
    items = []
    seen = set()

    jsonld_scripts = soup.select("script[type='application/ld+json']")
    jsonld_items = []
    for script in jsonld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                jsonld_items.append(data)
            elif isinstance(data, list):
                jsonld_items.extend(data)
        except (json.JSONDecodeError, TypeError):
            continue

    for data in jsonld_items:
        if not isinstance(data, dict) or data.get("@type") != "Product":
            continue
        name_val = data.get("name", "")
        if not name_val:
            continue
        offers = data.get("offers", {})
        if isinstance(offers, dict):
            price = offers.get("price", "")
        elif isinstance(offers, list) and offers:
            price = offers[0].get("price", "")
        else:
            price = ""
        image = ""
        if data.get("image"):
            img = data["image"]
            image = img if isinstance(img, str) else (img[0] if isinstance(img, list) and img else "")
        url = data.get("url", "")

        key = url or name_val
        if key in seen:
            continue
        seen.add(key)

        items.append({
            "title": name_val.strip(),
            "price_text": f"R$ {price}" if price else "",
            "seller_name": None,
            "listing_url": url or base_url,
        })

    if items:
        return items

    containers = soup.select("div.js-item-product, div.product-item, div[data-product-id], li.product, div.product")
    if not containers:
        containers = soup.select("a[href*='/produtos/']")
        containers = [c for c in containers if c.get("title") or c.get_text(strip=True)]
        containers = [{ "el": c } for c in containers[:30]]
    else:
        containers = containers[:30]

    for container in containers:
        try:
            if isinstance(container, dict):
                a_tag = container["el"]
                title = a_tag.get("title", "") or a_tag.get_text(strip=True)
                href = a_tag.get("href", "")
                parent = a_tag.parent
                text = parent.get_text() if parent else a_tag.get_text()
            else:
                a_tag = container.select_one("a[href*='/produtos/']") or container
                title = ""
                title_el = container.select_one("h2, h3, h4, .product-name, .item-title")
                if title_el:
                    title = title_el.get_text(strip=True)
                if not title:
                    title = a_tag.get("title", "") or a_tag.get_text(strip=True)
                href = a_tag.get("href", "") if hasattr(a_tag, "get") else ""
                text = container.get_text() if hasattr(container, "get_text") else ""

            if not title or title in seen:
                continue
            seen.add(title)

            full_url = href if href.startswith("http") else base_url + href

            price_match = re.search(r"R\$\s*[\d.,]+", text)
            price_text = price_match.group(0) if price_match else ""

            items.append({
                "title": title.strip(),
                "price_text": price_text,
                "seller_name": None,
                "listing_url": full_url,
            })
        except Exception as e:
            logger.debug("Nuvemshop: erro ao extrair item: %s", e)
            continue

    return items
