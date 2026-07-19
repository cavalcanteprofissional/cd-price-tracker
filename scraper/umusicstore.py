import logging
import re
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://www.umusicstore.com"
API_SEARCH = BASE_URL + "/api/catalog_system/pub/products/search/{}"


def search_umusicstore(search_query: str, _context=None) -> list[dict]:
    logger.info("Universal Music Store: buscando '%s'", search_query)

    items = _try_api(search_query)
    if items:
        return items

    logger.info("Universal Music Store: API sem resultados")
    return []


def _try_api(search_query: str) -> list[dict]:
    url = API_SEARCH.format(quote(search_query))

    try:
        resp = httpx.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            },
            timeout=30,
            follow_redirects=True,
        )

        if resp.status_code != 200:
            logger.warning("Universal Music Store: API retornou %s", resp.status_code)
            return []

        data = resp.json()
        if not data:
            return []

        if isinstance(data, dict):
            data = [data]

        items = []
        seen = set()
        for product in data:
            product_name = product.get("productName", "")
            if not product_name or product_name in seen:
                continue
            seen.add(product_name)

            items_result = product.get("items", [])
            if not items_result:
                continue

            first_item = items_result[0]
            sellers = first_item.get("sellers", [])
            if not sellers:
                continue

            comm_price = sellers[0].get("commertialOffer", {})
            price = comm_price.get("Price", 0)
            price_text = f"R$ {price:.2f}" if price else ""

            image_url = ""
            images = first_item.get("images", [])
            if images:
                image_url = images[0].get("imageUrl", "")

            detail_url = f"{BASE_URL}/{product.get('linkText', '')}/p"

            items.append({
                "title": product_name.strip(),
                "price_text": price_text,
                "seller_name": None,
                "listing_url": detail_url,
            })

        if items:
            logger.info("Universal Music Store: %d produtos via API", len(items))
            for item in items[:3]:
                logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])

        return items

    except Exception as e:
        logger.error("Universal Music Store: erro na API: %s", e)
        return []
