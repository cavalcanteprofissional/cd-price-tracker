import logging
import random
import time
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


ML_SEARCH_URL = "https://lista.mercadolivre.com.br/{}"
ML_API_URL = "https://api.mercadolibre.com/sites/MLB/search"
ML_API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

ML_SELECTORS = {
    "results": "ol.ui-search-layout > li.ui-search-layout__item",
    "results_fallback": "li.ui-search-layout__item",
    "title": ".ui-search-item__title",
    "price": ".andes-money-amount__fraction",
    "seller": ".ui-search-item__seller-info",
    "link": "a.ui-search-link",
}


def _extract_from_api(search_query: str) -> list[dict] | None:
    try:
        params = {"q": search_query, "limit": 20}
        resp = httpx.get(ML_API_URL, params=params, headers=ML_API_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            return None

        items = []
        for item in results:
            title = item.get("title", "").strip()
            price = item.get("price")
            currency_id = item.get("currency_id")
            permalink = item.get("permalink", "")
            seller = item.get("seller", {}).get("nickname") if item.get("seller") else None

            if not title or price is None:
                continue

            price_text = f"{price:.2f}"
            if currency_id == "BRL":
                pass  # preco ja em reais

            items.append({
                "title": title,
                "price_text": price_text,
                "seller_name": seller,
                "listing_url": permalink,
            })

        return items

    except Exception as e:
        logger.warning("ML API: erro na busca '%s': %s", search_query, e)
        return None


def _extract_from_page(page) -> list[dict]:
    items = page.query_selector_all(ML_SELECTORS["results"])
    if not items:
        items = page.query_selector_all(ML_SELECTORS["results_fallback"])

    if not items:
        logger.info("ML: nenhum resultado encontrado na pagina")
        return []

    results = []
    for item in items[:20]:
        try:
            title_el = item.query_selector(ML_SELECTORS["title"])
            price_el = item.query_selector(ML_SELECTORS["price"])
            seller_el = item.query_selector(ML_SELECTORS["seller"])
            link_el = item.query_selector(ML_SELECTORS["link"])

            if not title_el or not price_el:
                continue

            title = title_el.text_content().strip()
            price_text = price_el.text_content().strip()
            seller = seller_el.text_content().strip() if seller_el else None
            href = link_el.get_attribute("href") if link_el else None

            if href and not href.startswith("http"):
                href = "https://" + href.lstrip("/")

            results.append({
                "title": title,
                "price_text": price_text,
                "seller_name": seller,
                "listing_url": href or "",
            })
        except Exception as e:
            logger.debug("ML: erro ao extrair item: %s", e)
            continue

    return results


def scrape_mercadolivre(search_query: str, context) -> list[dict]:
    # Tentar API primeiro (nao requer browser, funciona sem anti-bot)
    api_results = _extract_from_api(search_query)
    if api_results:
        logger.info("ML: %d resultados via API para '%s'", len(api_results), search_query)
        return api_results

    # Fallback: Playwright (pode falhar com captcha)
    logger.info("ML: fallback para Playwright em '%s'", search_query)
    queries = [search_query]
    if " original" in search_query:
        queries.append(search_query.replace(" original", ""))

    seen_urls = set()
    all_results = []

    for q in queries:
        page = None
        try:
            page = context.new_page()
            page.set_default_timeout(30000)

            url = ML_SEARCH_URL.format(quote(q))
            logger.info("ML: buscando '%s' via Playwright em %s", q, url)

            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 4))
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            results = _extract_from_page(page)
            for r in results:
                if r["listing_url"] not in seen_urls:
                    seen_urls.add(r["listing_url"])
                    all_results.append(r)

            if all_results:
                return all_results

        except Exception as e:
            logger.error("ML: erro na busca '%s': %s", q, e)
        finally:
            if page:
                page.close()

    return all_results
