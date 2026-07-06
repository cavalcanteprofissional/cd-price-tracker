import logging
import random
import re
import time
import unicodedata
from urllib.parse import quote

logger = logging.getLogger(__name__)


AMAZON_SELECTORS = {
    "title": "#productTitle",
    "price_whole": ".a-price-whole",
    "price_fraction": ".a-price-fraction",
    "availability": "#availability span",
}

AMAZON_SEARCH_SELECTORS = {
    "results": "div[data-component-type='s-search-result']",
    "title": "h2 a",
    "price_offscreen": ".a-price .a-offscreen",
    "link": "h2 a",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s]", "", text)


def _token_similarity(a: str, b: str) -> float:
    a_tokens = set(_normalize(a).split())
    b_tokens = set(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    return len(intersection) / max(len(a_tokens), len(b_tokens))


def scrape_amazon(amazon_url: str, context) -> dict | None:
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(30000)

        delay = random.uniform(3, 7)
        logger.info("Amazon: aguardando %.1fs antes de acessar %s", delay, amazon_url)
        time.sleep(delay)

        page.goto(amazon_url, wait_until="domcontentloaded")
        time.sleep(random.uniform(2, 5))

        title_el = page.query_selector(AMAZON_SELECTORS["title"])
        if not title_el:
            logger.warning("Amazon: titulo nao encontrado em %s", amazon_url)
            return None
        title = title_el.text_content().strip()

        price_whole = page.query_selector(AMAZON_SELECTORS["price_whole"])
        price_fraction = page.query_selector(AMAZON_SELECTORS["price_fraction"])
        if not price_whole:
            logger.warning("Amazon: preco nao encontrado em %s", amazon_url)
            return None

        price_text = price_whole.text_content().strip()
        if price_fraction:
            price_text += "," + price_fraction.text_content().strip()

        availability_el = page.query_selector(AMAZON_SELECTORS["availability"])
        availability = "in_stock"
        if availability_el:
            avail_text = availability_el.text_content().strip().lower()
            if "fora" in avail_text or "indispon" in avail_text:
                availability = "out_of_stock"

        return {
            "title": title,
            "price_text": price_text,
            "availability": availability,
            "listing_url": amazon_url,
            "seller_name": None,
        }

    except Exception as e:
        logger.error("Amazon: erro ao acessar %s: %s", amazon_url, e)
        return None
    finally:
        if page:
            page.close()


def search_amazon(title: str, artist: str, context) -> dict | None:
    page = None
    try:
        search_term = f"{title} {artist} cd"
        logger.info("Amazon search: buscando '%s'", search_term)

        page = context.new_page()
        page.set_default_timeout(30000)

        url = f"https://www.amazon.com.br/s?k={quote(search_term)}"
        time.sleep(random.uniform(3, 7))
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(random.uniform(3, 6))

        result_divs = page.query_selector_all(AMAZON_SEARCH_SELECTORS["results"])
        if not result_divs:
            logger.warning("Amazon search: nenhum resultado para '%s'", search_term)
            return None

        candidates = []
        for item in result_divs[:10]:
            try:
                link_el = item.query_selector(AMAZON_SEARCH_SELECTORS["link"])
                if not link_el:
                    continue
                result_title = link_el.text_content().strip()
                href = link_el.get_attribute("href")
                if href and not href.startswith("http"):
                    href = "https://www.amazon.com.br" + href

                price_el = item.query_selector(AMAZON_SEARCH_SELECTORS["price_offscreen"])
                price_text = None
                if price_el:
                    price_text = price_el.text_content().strip()

                candidates.append({
                    "title": result_title,
                    "price_text": price_text,
                    "listing_url": href,
                })
            except Exception:
                continue

        if not candidates:
            logger.warning("Amazon search: nenhum candidato extraido para '%s'", search_term)
            return None

        expected = f"{title} {artist}"
        best = max(candidates, key=lambda c: _token_similarity(expected, c["title"]))
        best_score = _token_similarity(expected, best["title"])

        logger.info("Amazon search: melhor match (score=%.2f): '%s'", best_score, best["title"])

        if best_score < 0.3:
            logger.warning("Amazon search: confianca muito baixa (%.2f) para '%s'", best_score, search_term)
            return None

        if best["price_text"]:
            return {
                "title": best["title"],
                "price_text": best["price_text"],
                "availability": "in_stock",
                "listing_url": best["listing_url"],
                "seller_name": None,
            }

        logger.info("Amazon search: sem preco na busca, navegando ate a pagina do produto")
        time.sleep(random.uniform(2, 4))
        page.goto(best["listing_url"], wait_until="domcontentloaded")
        time.sleep(random.uniform(2, 4))

        price_whole = page.query_selector(AMAZON_SELECTORS["price_whole"])
        if not price_whole:
            logger.warning("Amazon search: preco nao encontrado na pagina do produto")
            return None

        price_text = price_whole.text_content().strip()
        price_fraction = page.query_selector(AMAZON_SELECTORS["price_fraction"])
        if price_fraction:
            price_text += "," + price_fraction.text_content().strip()

        return {
            "title": best["title"],
            "price_text": price_text,
            "availability": "in_stock",
            "listing_url": best["listing_url"],
            "seller_name": None,
        }

    except Exception as e:
        logger.error("Amazon search: erro ao buscar '%s - %s': %s", title, artist, e)
        return None
    finally:
        if page:
            page.close()
