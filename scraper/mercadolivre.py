import logging
import random
import time
from urllib.parse import quote

logger = logging.getLogger(__name__)


ML_SEARCH_URL = "https://lista.mercadolivre.com.br/{}"

ML_SELECTORS = {
    "results": "ol.ui-search-layout > li.ui-search-layout__item",
    "title": ".ui-search-item__title",
    "price": ".andes-money-amount__fraction",
    "seller": ".ui-search-item__seller-info",
    "link": "a.ui-search-link",
}


def scrape_mercadolivre(search_query: str, context) -> list[dict]:
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(30000)

        url = ML_SEARCH_URL.format(quote(search_query))
        logger.info("ML: buscando '%s' em %s", search_query, url)

        page.goto(url, wait_until="domcontentloaded")
        time.sleep(random.uniform(2, 4))

        items = page.query_selector_all(ML_SELECTORS["results"])
        if not items:
            logger.info("ML: nenhum resultado para '%s'", search_query)
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
                    "listing_url": href or url,
                })
            except Exception as e:
                logger.debug("ML: erro ao extrair item: %s", e)
                continue

        return results

    except Exception as e:
        logger.error("ML: erro na busca '%s': %s", search_query, e)
        return []
    finally:
        if page:
            page.close()
