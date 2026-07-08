import logging
import random
import re
import time
from urllib.parse import quote

from scraper.utils import normalize, token_similarity

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
        # Amazon as vezes inclui separador no final: "374." ou "374,"
        price_text = price_text.rstrip(".,")
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


def _extract_candidates(page) -> list[dict]:
    """Tenta extrair candidatos da pagina de busca Amazon com fallback de seletores."""
    candidates = []

    result_divs = page.query_selector_all(AMAZON_SEARCH_SELECTORS["results"])
    if not result_divs:
        return []

    # Tenta seletor primario (h2 a)
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

    if candidates:
        return candidates

    # Fallback: extrair via a[href*='/dp/'] dentro do result div
    # Amazon tem 2+ links /dp/ por item (imagem + titulo); pegar o que tiver texto
    logger.info("Amazon search: tentando fallback de seletores")
    for item in result_divs[:15]:
        try:
            link_els = item.query_selector_all("a[href*='/dp/']")
            link_el = None
            for le in link_els:
                txt = le.text_content().strip()
                if txt:
                    link_el = le
                    break
            if not link_el:
                continue
            result_title = link_el.text_content().strip()
            href = link_el.get_attribute("href")
            if not result_title or not href:
                continue
            if href and not href.startswith("http"):
                href = "https://www.amazon.com.br" + href

            price_el = item.query_selector(AMAZON_SEARCH_SELECTORS["price_offscreen"])
            price_text = None
            if price_el:
                price_text = price_el.text_content().strip()

            candidates.append({
                "title": result_title,
                "info": item.text_content().strip(),
                "price_text": price_text,
                "listing_url": href,
            })
        except Exception:
            continue

    return candidates


def _search_amazon_with_query(search_term: str, context) -> list | None:
    page = None
    try:
        logger.info("Amazon search: buscando '%s'", search_term)
        page = context.new_page()
        page.set_default_timeout(30000)

        url = f"https://www.amazon.com.br/s?k={quote(search_term)}"
        time.sleep(random.uniform(3, 7))
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(random.uniform(3, 6))

        # Scroll para carregar resultados
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        candidates = _extract_candidates(page)
        if not candidates:
            logger.warning("Amazon search: nenhum candidato extraido para '%s'", search_term)
            return None

        return candidates
    except Exception as e:
        logger.error("Amazon search: erro ao buscar '%s': %s", search_term, e)
        return None
    finally:
        if page:
            page.close()


def search_amazon(title: str, artist: str, context) -> dict | None:
    search_terms = [
        f"{title} {artist} cd original",
        f"{title} {artist} cd",
    ]

    all_candidates = []
    for term in search_terms:
        candidates = _search_amazon_with_query(term, context)
        if candidates:
            all_candidates.extend(candidates)
        if all_candidates:
            break

    if not all_candidates:
        return None

    expected = f"{title} {artist}"
    artist_tokens = set(normalize(artist).split())

    def candidate_score(c):
        score = token_similarity(expected, c["title"])
        if score > 0:
            return score
        # Se o titulo nao contem tokens do artista, verificar no texto completo
        info_text = c.get("info", "")
        if info_text:
            info_norm = normalize(info_text)
            if any(t in info_norm for t in artist_tokens):
                return 0.15  # bonus baixo por artista presente
        return 0.0

    best = max(all_candidates, key=candidate_score)
    best_score = candidate_score(best)

    logger.info("Amazon search: melhor match (score=%.2f): '%s'", best_score, best["title"])

    if best_score < 0.15:
        logger.warning("Amazon search: confianca muito baixa (%.2f) para '%s'", best_score, search_terms[0])
        return None

    if best["price_text"]:
        return {
            "title": best["title"],
            "price_text": best["price_text"],
            "availability": "in_stock",
            "listing_url": best["listing_url"],
            "seller_name": None,
        }

    # Sem preco na busca — navegar ate a pagina do produto
    logger.info("Amazon search: sem preco na busca, navegando ate a pagina do produto")
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(30000)

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
        logger.error("Amazon search: erro ao acessar pagina do produto: %s", e)
        return None
    finally:
        if page:
            page.close()
