import logging
import random
import time
from urllib.parse import quote

from scraper.utils import first_selector, normalize, token_similarity, best_match

logger = logging.getLogger(__name__)


MAGALU_URL = "https://www.magazineluiza.com.br/busca/{}"

MAGALU_SELECTORS = {
    "results": "[data-testid='product-card'], div[class*='product-card'], div[class*='ProductCard'], li[class*='product']",
    "title": "[data-testid='product-title'], h2[class*='product-title'], a[class*='ProductCard'], h2",
    "price": "[data-testid='price-value'], p[class*='price'], div[class*='Price'], span[class*='price']",
    "link": "a[data-testid='product-card'], a[class*='ProductCard'], a[href*='/produto/'], a[href*='/p/']",
    "seller": "[data-testid='seller-name'], span[class*='seller']",
}


def _extract_from_page(page) -> list[dict]:
    logger.info("Magalu: extraindo candidatos da pagina")
    all_items = []

    # Tentar cada seletor de resultados
    selectors = [s.strip() for s in MAGALU_SELECTORS["results"].split(",")]
    results = None
    for sel in selectors:
        results = page.query_selector_all(sel)
        if results:
            logger.info("Magalu: %d resultados com seletor '%s'", len(results), sel)
            break

    if not results:
        return []

    for item in results[:20]:
        try:
            title_el = first_selector(item, [
                "[data-testid='product-title']",
                "h2",
                "a[class*='ProductCard']",
                "[class*='title']",
                "[class*='name']",
            ])
            if not title_el:
                continue
            title = title_el.text_content().strip()
            if not title:
                continue

            price_el = first_selector(item, [
                "[data-testid='price-value']",
                "[class*='price']",
                "[class*='Price']",
                "p[class*='price']",
                "span[class*='price']",
            ])
            price_text = price_el.text_content().strip() if price_el else None

            link_el = first_selector(item, [
                "a[data-testid='product-card']",
                "a[href*='/produto/']",
                "a[href*='/p/']",
                "a",
            ])
            href = link_el.get_attribute("href") if link_el else None
            if href and not href.startswith("http"):
                href = "https://www.magazineluiza.com.br" + href

            seller_el = first_selector(item, [
                "[data-testid='seller-name']",
                "[class*='seller']",
                "[class*='Seller']",
            ])
            seller = seller_el.text_content().strip() if seller_el else None

            all_items.append({
                "title": title,
                "price_text": price_text,
                "seller_name": seller,
                "listing_url": href or "",
            })
        except Exception as e:
            logger.debug("Magalu: erro ao extrair item: %s", e)
            continue

    return all_items





def search_magalu(search_query: str, context) -> list[dict]:
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(45000)

        url = MAGALU_URL.format(quote(search_query))
        logger.info("Magalu: buscando '%s'", search_query)

        page.goto(url, wait_until="networkidle")

        html = page.content()
        if "Nao e possivel acessar" in html or "error-code\">403" in html:
            logger.warning("Magalu: bloqueado por anti-bot (Akamai 403)")
            return []

        page.wait_for_timeout(3000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        candidates = _extract_from_page(page)
        if not candidates:
            logger.warning("Magalu: nenhum candidato encontrado para '%s'", search_query)
            return []

        expected = search_query.replace(" cd original", "").replace(" cd", "")
        best = best_match(candidates, expected, search_query)
        return [best] if best else []

    except Exception as e:
        logger.error("Magalu: erro na busca '%s': %s", search_query, e)
        return []
    finally:
        if page:
            page.close()
