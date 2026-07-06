import logging
import random
import re
import time
from urllib.parse import quote

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
            title_el = _first_selector(item, [
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

            price_el = _first_selector(item, [
                "[data-testid='price-value']",
                "[class*='price']",
                "[class*='Price']",
                "p[class*='price']",
                "span[class*='price']",
            ])
            price_text = price_el.text_content().strip() if price_el else None

            link_el = _first_selector(item, [
                "a[data-testid='product-card']",
                "a[href*='/produto/']",
                "a[href*='/p/']",
                "a",
            ])
            href = link_el.get_attribute("href") if link_el else None
            if href and not href.startswith("http"):
                href = "https://www.magazineluiza.com.br" + href

            seller_el = _first_selector(item, [
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


def _first_selector(parent, selectors: list[str]):
    for sel in selectors:
        el = parent.query_selector(sel)
        if el:
            return el
    return None


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text


def _token_similarity(a: str, b: str) -> float:
    a_tokens = set(_normalize(a).split())
    b_tokens = set(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    return len(intersection) / max(len(a_tokens), len(b_tokens))


def _best_match(candidates: list[dict], expected: str, artist: str) -> dict | None:
    if not candidates:
        return None
    artist_tokens = set(_normalize(artist).split())

    def score(c):
        s = _token_similarity(expected, c["title"])
        if s <= 0 and artist_tokens:
            info_norm = _normalize(c.get("_info", ""))
            if any(t in info_norm for t in artist_tokens):
                s = 0.15
        return s

    best = max(candidates, key=score)
    best_score = score(best)
    logger.info("Magalu: melhor match (score=%.2f): '%s'", best_score, best["title"])
    return best if best_score >= 0.15 else None


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
        best = _best_match(candidates, expected, search_query)
        return [best] if best else []

    except Exception as e:
        logger.error("Magalu: erro na busca '%s': %s", search_query, e)
        return []
    finally:
        if page:
            page.close()
