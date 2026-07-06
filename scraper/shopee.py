import json
import logging
import random
import re
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


def _extract_from_initial_state(page) -> list[dict] | None:
    """Extrai dados JSON embutidos no HTML (__INITIAL_STATE__, __NEXT_DATA__, JSON-LD)."""
    try:
        content = page.content()

        # Tentar __NEXT_DATA__ (Next.js SSR)
        match = re.search(
            r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            content, re.DOTALL,
        )
        if match:
            data = json.loads(match.group(1))
            items = _drill_items(data)
            if items:
                return items

        # Tentar window.__INITIAL_STATE__ (SPA preloaded state)
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', content, re.DOTALL)
        if match:
            state = json.loads(match.group(1))
            items = _drill_items(state)
            if items:
                return items

        # Tentar JSON-LD (schema.org)
        matches = re.findall(
            r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
            content, re.DOTALL,
        )
        for m in matches:
            try:
                data = json.loads(m)
                items_list = data.get("itemListElement", [])
                if not items_list:
                    continue
                results = []
                for entry in items_list:
                    item = entry.get("item", {})
                    name = item.get("name", "")
                    url = item.get("url", "")
                    offers = item.get("offers", {})
                    price = offers.get("price")
                    if not name or not price:
                        continue
                    results.append({
                        "title": name.strip(),
                        "price_text": f"{float(price):.2f}",
                        "seller_name": None,
                        "listing_url": url,
                    })
                if results:
                    logger.info("Shopee initial state: %d via JSON-LD", len(results))
                    return results
            except Exception:
                continue

    except Exception as e:
        logger.debug("Shopee initial state: erro: %s", e)
    return None


def _drill_items(data: dict) -> list[dict] | None:
    """Procura items em varias profundidades do estado."""
    # Caminhos comuns onde items podem estar
    paths = [
        ["props", "pageProps", "searchResult", "items"],
        ["props", "pageProps", "initialState", "searchResult", "items"],
        ["searchResult", "items"],
        ["search", "items"],
        ["items"],
    ]
    for path in paths:
        cur = data
        try:
            for key in path:
                cur = cur[key]
            if isinstance(cur, list) and len(cur) > 0:
                results = []
                for item in cur:
                    name = item.get("name", item.get("title", ""))
                    price = item.get("price") or item.get("price_min", 0) or item.get("price_max", 0)
                    itemid = item.get("itemid")
                    shopid = item.get("shopid")
                    if not name or not price:
                        continue
                    listing_url = f"https://shopee.com.br/product/{shopid}/{itemid}"
                    results.append({
                        "title": name.strip(),
                        "price_text": f"{float(price)/100000:.2f}",
                        "seller_name": str(shopid) if shopid else None,
                        "listing_url": listing_url,
                    })
                if results:
                    logger.info("Shopee initial state: %d via path %s", len(results), ".".join(path))
                    return results
        except (KeyError, TypeError, IndexError):
            continue
    return None


def _extract_from_page(search_query: str, context) -> list[dict]:
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(45000)

        url = f"https://shopee.com.br/search?keyword={quote(search_query)}"
        logger.info("Shopee page: buscando '%s'", search_query)

        page.goto(url, wait_until="networkidle")
        time.sleep(random.uniform(3, 5))

        # Tentar extrair do estado inicial (funciona mesmo se SPA nao renderizar)
        items = _extract_from_initial_state(page)
        if items:
            return items

        # Fallback: tentar seletores DOM
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        selectors = [
            "div.shopee-search-item-result__item",
            "[data-sqe='item']",
            "div[class*='search-item']",
            "div[class*='product-item']",
        ]
        found = None
        for sel in selectors:
            if page.query_selector(sel):
                found = sel
                break

        if not found:
            logger.info("Shopee page: nenhum seletor encontrado")
            return []

        items = page.query_selector_all(found)
        results = []
        for item in items[:20]:
            try:
                title_el = _first_selector(item, [
                    "div[data-sqe='name']",
                    "div[class*='name']",
                    "div[class*='title']",
                ])
                if not title_el:
                    continue
                title = title_el.text_content().strip()

                price_el = _first_selector(item, [
                    "span[data-sqe='price']",
                    "span[class*='price']",
                    "div[class*='price']",
                ])
                price_text = price_el.text_content().strip() if price_el else "0"

                link_el = _first_selector(item, [
                    "a[data-sqe='link']",
                    "a[class*='item-link']",
                    "a[href*='/product/']",
                ])
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
                logger.debug("Shopee page: erro ao extrair item: %s", e)
                continue

        logger.info("Shopee page: %d resultados via DOM", len(results))
        return results

    except Exception as e:
        logger.error("Shopee page: erro '%s': %s", search_query, e)
        return []
    finally:
        if page:
            page.close()


def _first_selector(parent, selectors: list[str]):
    for sel in selectors:
        el = parent.query_selector(sel)
        if el:
            return el
    return None


def scrape_shopee(search_query: str, context) -> list[dict]:
    # 1. Tentar API direta (quase sempre 403, mas tentar nao custa)
    api_results = _extract_from_api(search_query)
    if api_results is not None:
        return api_results

    # 2. Via Playwright com networkidle + initial state (melhor chance)
    logger.info("Shopee: tentando extracao via pagina")
    return _extract_from_page(search_query, context)
