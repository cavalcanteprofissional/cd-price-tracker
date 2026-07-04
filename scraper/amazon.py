import logging
import random
import time

logger = logging.getLogger(__name__)


AMAZON_SELECTORS = {
    "title": "#productTitle",
    "price_whole": ".a-price-whole",
    "price_fraction": ".a-price-fraction",
    "availability": "#availability span",
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
