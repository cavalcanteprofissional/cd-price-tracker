import logging
import random
import re
import time
from urllib.parse import quote

import httpx

from scraper.mercadolivre_api import MercadoLivreAPIClient

logger = logging.getLogger(__name__)


def try_mercadolivre_api(search_query: str) -> list[dict] | None:
    """Tenta API oficial com OAuth. Se nao configurada ou falhar, retorna None."""
    client = MercadoLivreAPIClient()
    return client.search_with_fallback(search_query)


ML_DESKTOP_URL = "https://lista.mercadolivre.com.br/{}"
ML_API_URL = "https://api.mercadolibre.com/sites/MLB/search"
ML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

ML_SELECTORS = {
    "results": "ol.ui-search-layout > li.ui-search-layout__item",
    "results_fallback": "li.ui-search-layout__item",
    "title": ".ui-search-item__title",
    "price": ".andes-money-amount__fraction",
    "seller": ".ui-search-item__seller-info",
    "link": "a.ui-search-link",
}


def _extract_from_api_public(search_query: str) -> list[dict] | None:
    """Tenta a API publica sem autenticacao (quase sempre 403)."""
    try:
        params = {"q": search_query, "limit": 20}
        resp = httpx.get(ML_API_URL, params=params, headers=ML_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        items = []
        for item in results:
            title = item.get("title", "").strip()
            price = item.get("price")
            permalink = item.get("permalink", "")
            seller = item.get("seller", {}).get("nickname") if item.get("seller") else None
            if not title or price is None:
                continue
            items.append({
                "title": title,
                "price_text": f"{price:.2f}",
                "seller_name": seller,
                "listing_url": permalink,
            })
        return items
    except Exception as e:
        logger.debug("ML API publica: erro na busca '%s': %s", search_query, e)
        return None


def _extract_from_page(page) -> list[dict]:
    items = page.query_selector_all(ML_SELECTORS["results"])
    if not items:
        items = page.query_selector_all(ML_SELECTORS["results_fallback"])
    if not items:
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
    # 1. Tentar API oficial com OAuth (se configurada)
    api_client = MercadoLivreAPIClient()
    oauth_results = api_client.search_with_fallback(search_query)
    if oauth_results is not None:
        logger.info("ML: %d resultados via API oficial", len(oauth_results))
        return oauth_results

    # 2. Tentar API publica (geralmente 403, mas tentar nao custa)
    api_results = _extract_from_api_public(search_query)
    if api_results:
        logger.info("ML: %d resultados via API publica", len(api_results))
        return api_results

    # 3. Via Playwright (geralmente bloqueado por CAPTCHA)
    logger.info("ML: tentando via Playwright")
    queries = [search_query]
    if " original" in search_query:
        queries.append(search_query.replace(" original", ""))

    for q in queries:
        page = None
        try:
            page = context.new_page()
            page.set_default_timeout(30000)

            url = ML_DESKTOP_URL.format(quote(q))
            logger.info("ML desktop: buscando '%s' em %s", q, url)

            resp = page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 4))

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            items = _extract_from_page(page)
            if items:
                logger.info("ML desktop: %d resultados", len(items))
                return items

            title = page.title()
            content_preview = page.content()[:500].lower()
            if "captcha" in content_preview:
                logger.warning("ML: CAPTCHA detectado (title='%s')", title)
            else:
                logger.info("ML: sem resultados (title='%s')", title)

        except Exception as e:
            logger.error("ML: erro: %s", e)
        finally:
            if page:
                page.close()

    return []
