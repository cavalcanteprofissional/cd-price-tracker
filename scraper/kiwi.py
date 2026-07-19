import logging
import re
from urllib.parse import quote

from scraper.utils import normalize, token_similarity, best_match

logger = logging.getLogger(__name__)

BASE_URL = "https://www.kiwidiscos.com.br"
SEARCH_URL = BASE_URL + "/busca/?q={}"

PRODUCT_SELECTOR = (
    "a.js-item-product, a.item-product, [class*='product'] a[href*='/produtos/'], "
    "a[href*='/produto/'], article a[href*='/produtos/'], div[class*='product'] a"
)
WAIT_SELECTOR = (
    "a.js-item-product, a.item-product, [class*='product'], "
    "main, [role='main'], article, .products-row, .product-grid"
)

PRICE_SELECTORS = [
    "[class*='price']",
    "[class*='Price']",
    "[class*='preco']",
    "[class*='Preco']",
    "span.value",
    "strong[class*='price']",
]


def _log_diagnostics(page, search_query: str):
    try:
        info = page.evaluate("""() => {
            const allLinks = Array.from(document.querySelectorAll('a')).map(a => ({
                href: a.getAttribute('href') || '',
                text: (a.textContent || '').trim().slice(0, 80)
            }));
            const bodyText = document.body ? document.body.innerText : '';
            const priceCount = (bodyText.match(/R\\$/g) || []).length;
            return {
                title: document.title,
                url: window.location.href,
                totalLinks: allLinks.length,
                priceCount: priceCount,
                bodyPreview: bodyText.slice(0, 500)
            };
        }""")

        logger.info("=== KIWI DIAGNOSTIC ===")
        logger.info("Title: %s", info["title"])
        logger.info("URL: %s", info["url"])
        logger.info("Links: %d, R$ occurrences: %d", info["totalLinks"], info["priceCount"])
        logger.info("Body preview: %s", info["bodyPreview"][:200].replace("\n", " | "))

        product_links = [l for l in info["allLinks"] if "/produto" in l["href"] or "/produtos" in l["href"]]
        logger.info("Product links: %d", len(product_links))
        for l in product_links[:5]:
            logger.info("  %s | '%s'", l["href"], l["text"])
    except Exception as e:
        logger.warning("Kiwi: erro no diagnostico: %s", e)


def search_kiwi(search_query: str, context) -> list[dict]:
    logger.info("Kiwi: buscando '%s'", search_query)
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(45000)

        url = SEARCH_URL.format(quote(search_query))
        logger.info("Kiwi: navegando para %s", url)

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        _log_diagnostics(page, search_query)

        try:
            page.wait_for_function(
                "() => document.querySelector('a[href*=\"/produto\"]') || "
                "document.querySelector('[class*=\"product\"]') || "
                "document.body.innerText.includes('R$')",
                timeout=15000
            )
        except Exception:
            logger.warning("Kiwi: timeout esperando conteudo renderizar")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        items = _extract_from_page(page)

        if items:
            logger.info("Kiwi: %d candidatos extraidos", len(items))
            for item in items[:3]:
                logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])
        else:
            logger.warning("Kiwi: nenhum candidato encontrado")

        return items
    except Exception as e:
        logger.error("Kiwi: erro na busca: %s", e)
        return []
    finally:
        if page:
            page.close()


def _extract_from_page(page) -> list[dict]:
    items = []

    try:
        result = page.evaluate("""() => {
            const productLinks = document.querySelectorAll('a[href*="/produto"], a[href*="/produtos"]');
            const results = [];
            const seen = new Set();

            for (const link of productLinks) {
                const href = link.getAttribute('href') || '';
                const fullHref = href.startsWith('http') ? href : 'https://www.kiwidiscos.com.br' + href;
                if (seen.has(fullHref)) continue;
                seen.add(fullHref);

                const card = link.closest('article, div[class*="product"], div[class*="item"], li') || link;
                const text = card.textContent || link.textContent || '';

                let price = '';
                const priceMatch = text.match(/R\\$\\s*[\\d.,]+/);
                if (priceMatch) price = priceMatch[0];

                const title = (link.textContent || '').trim() || text.slice(0, 100).trim();

                results.push({ title, price, href: fullHref });
            }
            return results.slice(0, 30);
        }""")

        for item in result:
            items.append({
                "title": item["title"],
                "price_text": item["price"],
                "seller_name": None,
                "listing_url": item["href"],
            })
    except Exception as e:
        logger.warning("Kiwi: erro no evaluate: %s", e)

    return items
