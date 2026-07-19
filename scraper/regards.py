import logging
import re
from urllib.parse import quote

from scraper.utils import normalize, token_similarity, best_match

logger = logging.getLogger(__name__)

BASE_URL = "https://www.regards.com.br"
SEARCH_URL = BASE_URL + "/?s={}&post_type=product"

PRODUCT_SELECTOR = (
    "a[href*='/produto/'], a[href*='/product/'], "
    "li.product a, .product a, .type-product a"
)


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

        logger.info("=== REGARDS DIAGNOSTIC ===")
        logger.info("Title: %s", info["title"])
        logger.info("URL: %s", info["url"])
        logger.info("Links: %d, R$: %d", info["totalLinks"], info["priceCount"])

        product_links = [l for l in info["allLinks"] if "/produto" in l["href"] or "/product" in l["href"]]
        logger.info("Product links: %d", len(product_links))
        for l in product_links[:5]:
            logger.info("  %s | '%s'", l["href"], l["text"])
    except Exception as e:
        logger.warning("Regards: erro diagnostico: %s", e)


def search_regards(search_query: str, context) -> list[dict]:
    logger.info("Regards: buscando '%s'", search_query)
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(45000)

        url = SEARCH_URL.format(quote(search_query))
        logger.info("Regards: navegando para %s", url)

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        _log_diagnostics(page, search_query)

        try:
            page.wait_for_function(
                "() => document.querySelector('a[href*=\"/produto\"]') || "
                "document.querySelector('li.product, .product, .type-product') || "
                "document.body.innerText.includes('R$')",
                timeout=15000
            )
        except Exception:
            logger.warning("Regards: timeout esperando conteudo")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        items = _extract_from_page(page)

        if items:
            logger.info("Regards: %d candidatos extraidos", len(items))
            for item in items[:3]:
                logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])
        else:
            logger.warning("Regards: nenhum candidato encontrado")

        return items
    except Exception as e:
        logger.error("Regards: erro na busca: %s", e)
        return []
    finally:
        if page:
            page.close()


def _extract_from_page(page) -> list[dict]:
    items = []

    try:
        result = page.evaluate("""() => {
            const productSelectors = [
                'li.product', '.product', '.type-product',
                'div[class*="product"]', 'article[class*="product"]'
            ];
            let products = [];
            for (const sel of productSelectors) {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    products = Array.from(els);
                    break;
                }
            }

            if (products.length === 0) {
                const links = document.querySelectorAll('a[href*="/produto"], a[href*="/product"]');
                products = Array.from(links).map(l => l.closest('li, div, article') || l);
            }

            const results = [];
            const seen = new Set();

            for (const product of products) {
                const link = product.querySelector('a[href*="/produto"], a[href*="/product"]') || product;
                const href = link.getAttribute('href') || '';
                if (!href || seen.has(href)) continue;
                seen.add(href);

                const text = product.textContent || '';
                const priceMatch = text.match(/R\\$\\s*[\\d.,]+/);
                const price = priceMatch ? priceMatch[0] : '';

                let title = '';
                const titleEl = product.querySelector('h2, h3, .product-title, .woocommerce-loop-product__title');
                if (titleEl) title = titleEl.textContent.trim();

                results.push({ title, price, href });
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
        logger.warning("Regards: erro no evaluate: %s", e)

    return items
