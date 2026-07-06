import logging
import random
import time
from urllib.parse import quote

from scraper.amazon import _extract_candidates, scrape_amazon as _scrape_amazon_product

logger = logging.getLogger(__name__)


MARKETPLACES = {
    "amazon_us": {
        "domain": "amazon.com",
        "search_url": "https://www.amazon.com/s?k={}",
        "currency": "USD",
        "name": "Amazon US",
    },
    "amazon_uk": {
        "domain": "amazon.co.uk",
        "search_url": "https://www.amazon.co.uk/s?k={}",
        "currency": "GBP",
        "name": "Amazon UK",
    },
    "amazon_de": {
        "domain": "amazon.de",
        "search_url": "https://www.amazon.de/s?k={}",
        "currency": "EUR",
        "name": "Amazon DE",
    },
}


def search_amazon_marketplace(title: str, artist: str, context, marketplace: str) -> dict | None:
    cfg = MARKETPLACES.get(marketplace)
    if not cfg:
        logger.warning("Amazon global: marketplace desconhecido '%s'", marketplace)
        return None

    search_terms = [
        f"{title} {artist} cd",
        f"{title} {artist} album",
    ]

    all_candidates = []
    for term in search_terms:
        candidates = _search_with_query(term, context, cfg)
        if candidates:
            all_candidates.extend(candidates)
        if all_candidates:
            break

    if not all_candidates:
        logger.info("Amazon %s: nenhum resultado para '%s %s'", marketplace, title, artist)
        return None

    expected = f"{title} {artist}"
    best = max(all_candidates, key=lambda c: _token_similarity(expected, c["title"]))
    best_score = _token_similarity(expected, best["title"])

    logger.info("Amazon %s: melhor match (score=%.2f): '%s'", marketplace, best_score, best["title"])

    if best_score < 0.15:
        logger.warning("Amazon %s: confianca muito baixa (%.2f)", marketplace, best_score)
        return None

    if best["price_text"]:
        return {
            "title": best["title"],
            "price_text": best["price_text"],
            "availability": "in_stock",
            "listing_url": best["listing_url"],
            "seller_name": None,
            "currency": cfg["currency"],
        }

    logger.info("Amazon %s: sem preco na busca, navegando ate a pagina do produto", marketplace)
    return _scrape_product_page(best["listing_url"], context, marketplace)


def _search_with_query(search_term: str, context, cfg: dict) -> list[dict]:
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(30000)

        url = cfg["search_url"].format(quote(search_term))
        logger.info("Amazon %s: buscando '%s'", cfg["name"], search_term)

        time.sleep(random.uniform(3, 7))
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(random.uniform(3, 6))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        candidates = _extract_candidates(page)
        if candidates:
            for c in candidates:
                c["currency"] = cfg["currency"]
                # _extract_candidates do amazon.py prefixa com .com.br
                # Corrigir para o domínio do marketplace correto
                if c.get("listing_url"):
                    c["listing_url"] = c["listing_url"].replace(
                        "https://www.amazon.com.br",
                        f"https://www.{cfg['domain']}",
                    )
        return candidates or []
    finally:
        if page:
            page.close()


def _scrape_product_page(product_url: str, context, marketplace: str) -> dict | None:
    result = _scrape_amazon_product(product_url, context)
    if result:
        cfg = MARKETPLACES.get(marketplace, {})
        result["currency"] = cfg.get("currency", "USD")
    return result


def _token_similarity(a: str, b: str) -> float:
    from scraper.amazon import _token_similarity as _ts
    return _ts(a, b)
