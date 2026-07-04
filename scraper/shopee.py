import json
import logging
import random
import time
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


SHOPEE_SEARCH_API = "https://shopee.com.br/api/v4/search/search_items"
SHOPEE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "x-request-source": "desktop",
    "Referer": "https://shopee.com.br/",
    "Accept": "application/json",
}


def _extract_from_api(search_query: str) -> list[dict] | None:
    params = {
        "by": "relevancy",
        "keyword": search_query,
        "limit": 20,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
    }
    try:
        resp = httpx.get(
            SHOPEE_SEARCH_API,
            params=params,
            headers=SHOPEE_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        if not items:
            return None

        results = []
        for entry in items:
            basic = entry.get("item_basic", {})
            name = basic.get("name")
            price_raw = basic.get("price")
            shopid = basic.get("shopid")
            itemid = basic.get("itemid")

            if not name or not price_raw:
                continue

            price = price_raw / 100_000
            listing_url = f"https://shopee.com.br/product/{shopid}/{itemid}"

            results.append({
                "title": name.strip(),
                "price_text": f"{price:.2f}",
                "seller_name": str(shopid),
                "listing_url": listing_url,
            })

        return results

    except Exception as e:
        logger.warning("Shopee API: erro na busca '%s': %s", search_query, e)
        return None


def _extract_from_page(search_query: str, context) -> list[dict]:
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(30000)

        url = f"https://shopee.com.br/search?keyword={quote(search_query)}"
        logger.info("Shopee fallback: buscando '%s' via Playwright", search_query)

        page.goto(url, wait_until="domcontentloaded")
        time.sleep(random.uniform(3, 6))

        items = page.query_selector_all("div.shopee-search-item-result__item")
        results = []
        for item in items[:20]:
            try:
                title_el = item.query_selector("div[data-sqe='name']")
                price_el = item.query_selector("span[data-sqe='price']")
                link_el = item.query_selector("a[data-sqe='link']")

                if not title_el:
                    continue

                title = title_el.text_content().strip()
                price_text = price_el.text_content().strip() if price_el else "0"
                href = link_el.get_attribute("href") if link_el else None
                if href and not href.startswith("http"):
                    href = "https://shopee.com.br" + href

                results.append({
                    "title": title,
                    "price_text": price_text,
                    "seller_name": None,
                    "listing_url": href or url,
                })
            except Exception as e:
                logger.debug("Shopee fallback: erro ao extrair item: %s", e)
                continue

        return results

    except Exception as e:
        logger.error("Shopee fallback: erro '%s': %s", search_query, e)
        return []
    finally:
        if page:
            page.close()


def scrape_shopee(search_query: str, context) -> list[dict]:
    results = _extract_from_api(search_query)
    if results is not None:
        logger.info("Shopee: %d resultados via API para '%s'", len(results), search_query)
        return results

    logger.info("Shopee: fallback para Playwright em '%s'", search_query)
    return _extract_from_page(search_query, context)
