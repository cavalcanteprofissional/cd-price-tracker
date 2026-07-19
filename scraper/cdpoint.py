import logging
import re
from urllib.parse import quote

from scraper.utils import normalize, token_similarity, best_match

logger = logging.getLogger(__name__)

BASE_URL = "https://www.cdpoint.com.br"
SEARCH_URL = BASE_URL + "/Webforms/CDNFormularioPesquisa.aspx"


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

        logger.info("=== CDPOINT DIAGNOSTIC ===")
        logger.info("Title: %s", info["title"])
        logger.info("URL: %s", info["url"])
        logger.info("Links: %d, R$: %d", info["totalLinks"], info["priceCount"])
        logger.info("Body preview: %s", info["bodyPreview"][:300].replace("\n", " | "))

        product_links = [l for l in info["allLinks"] if "/CD/" in l["href"] or "/CDNListagem" in l["href"]]
        logger.info("CD links: %d", len(product_links))
        for l in product_links[:5]:
            logger.info("  %s | '%s'", l["href"], l["text"])
    except Exception as e:
        logger.warning("CDPoint: erro diagnostico: %s", e)


def _extract_from_page(page) -> list[dict]:
    items = []

    try:
        result = page.evaluate("""() => {
            const productRows = document.querySelectorAll('.comprados');
            const results = [];
            const seen = new Set();

            for (const row of productRows) {
                const link = row.querySelector('h3 a, h4 a, a[href*="/CD/"]');
                if (!link) continue;
                const href = link.getAttribute('href') || '';
                if (!href || seen.has(href)) continue;
                seen.add(href);

                const fullHref = href.startsWith('http') ? href : 'https://www.cdpoint.com.br' + href;
                const artistEl = row.querySelector('h3 a');
                const titleEl = row.querySelector('h4 a');
                const priceEl = row.querySelector('.preco');

                const artist = artistEl ? artistEl.textContent.trim() : '';
                const title = titleEl ? titleEl.textContent.trim() : '';
                const priceText = priceEl ? priceEl.textContent.trim() : '';

                results.push({
                    title: (artist + ' - ' + title).trim(),
                    price: priceText,
                    href: fullHref
                });
            }

            if (results.length === 0) {
                const allLinks = document.querySelectorAll('a[href*="/CD/"]');
                for (const link of allLinks) {
                    const href = link.getAttribute('href') || '';
                    if (!href || seen.has(href)) continue;
                    seen.add(href);

                    const fullHref = href.startsWith('http') ? href : 'https://www.cdpoint.com.br' + href;
                    const text = link.textContent.trim();
                    const row = link.closest('div, li, td') || link.parentElement;
                    const rowText = row ? row.textContent : text;
                    const priceMatch = rowText.match(/R\\$\\s*[\\d.,]+/);
                    const price = priceMatch ? priceMatch[0] : '';

                    results.push({ title: text || 'CD', price, href: fullHref });
                }
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
        logger.warning("CDPoint: erro no evaluate: %s", e)

    return items


def search_cdpoint(search_query: str, context) -> list[dict]:
    logger.info("CDPoint: buscando '%s'", search_query)
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(60000)

        logger.info("CDPoint: navegando para formulario de busca %s", SEARCH_URL)
        page.goto(SEARCH_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        search_input = page.query_selector("#txtBusca")
        if not search_input:
            logger.warning("CDPoint: campo de busca #txtBusca nao encontrado")
            page.wait_for_timeout(2000)
            search_input = page.query_selector("#txtBusca")

        if search_input:
            search_input.fill(search_query)
            page.wait_for_timeout(500)

            media_dropdown = page.query_selector("#ucrMidia_ddlMidia")
            if media_dropdown:
                media_dropdown.select_option("1")
                page.wait_for_timeout(500)

            logger.info("CDPoint: clicando no botao de pesquisa")
            search_btn = page.query_selector("#imgBtoPesquisa")
            if search_btn:
                search_btn.click()
            else:
                page.evaluate("__doPostBack('ctl00$imgBtoPesquisa','')")

            page.wait_for_timeout(5000)
        else:
            logger.warning("CDPoint: nao foi possivel encontrar campo de busca, tentando URL direta")
            direct_url = (
                BASE_URL + "/Webforms/CDNListagem.aspx?cod=25"
            )
            page.goto(direct_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

        _log_diagnostics(page, search_query)

        try:
            page.wait_for_function(
                "() => document.querySelector('.comprados, a[href*=\"/CD/\"], .preco')",
                timeout=15000
            )
        except Exception:
            logger.warning("CDPoint: timeout esperando resultados")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        items = _extract_from_page(page)

        if items:
            logger.info("CDPoint: %d candidatos extraidos", len(items))
            for item in items[:3]:
                logger.info("  exemplo: '%s' | preco='%s'", item["title"], item["price_text"])
        else:
            logger.warning("CDPoint: nenhum candidato encontrado")

        return items
    except Exception as e:
        logger.error("CDPoint: erro na busca: %s", e)
        return []
    finally:
        if page:
            page.close()
