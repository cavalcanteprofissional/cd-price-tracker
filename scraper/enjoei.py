import json
import logging
import os
import re
import tempfile
from urllib.parse import quote, urlparse

logger = logging.getLogger(__name__)

ENJOEI_URL = "https://www.enjoei.com.br/s?q={}"
ENJOEI_PRODUCT_LINK = "a[href*='/p/'], a[href*='/produto/'], a[href*='/item/']"
ENJOEI_WAIT_SELECTOR = (
    "a[href*='/p/'], a[href*='/produto/'], [class*='sc-'], "
    "[class*='card'], main, [role='main'], [data-testid]"
)


def _dump_html(page, search_query: str):
    try:
        html = page.content()
        safe = re.sub(r'[<>:"/\\|?*]', "_", search_query)[:50]
        tmp = tempfile.gettempdir()
        path = os.path.join(tmp, f"enjoei_{safe}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Enjoei: HTML salvo em %s (%d bytes)", path, len(html))
    except Exception as e:
        logger.warning("Enjoei: erro ao salvar HTML: %s", e)


def _log_diagnostics(page, search_query: str):
    try:
        info = page.evaluate("""() => {
            const allLinks = Array.from(document.querySelectorAll('a')).map(a => ({
                href: a.getAttribute('href') || '',
                text: (a.textContent || '').trim().slice(0, 80)
            }));
            const bodyText = document.body ? document.body.innerText : '';
            const priceCount = (bodyText.match(/R\\$/g) || []).length;
            const scElements = document.querySelectorAll('[class*="sc-"]').length;
            const allClasses = Array.from(document.querySelectorAll('[class]'))
                .slice(0, 50)
                .map(el => (el.getAttribute('class') || '').slice(0, 100));
            return {
                title: document.title,
                url: window.location.href,
                allLinks: allLinks.slice(0, 40),
                totalLinks: allLinks.length,
                priceCount: priceCount,
                scElementCount: scElements,
                sampleClasses: [...new Set(allClasses)].slice(0, 20),
                bodyPreview: bodyText.slice(0, 500)
            };
        }""")

        logger.info("=== ENJOEI DIAGNOSTIC ===")
        logger.info("Page title: %s", info["title"])
        logger.info("Page URL: %s", info["url"])
        logger.info("Total <a> links: %d", info["totalLinks"])
        logger.info("Occurrences of R$: %d", info["priceCount"])
        logger.info("Elements with sc- class: %d", info["scElementCount"])
        logger.info("Sample classes: %s", info["sampleClasses"])

        links_with_p = [l for l in info["allLinks"] if "/p/" in l["href"]]
        logger.info("Links containing /p/: %d", len(links_with_p))
        for l in links_with_p[:10]:
            logger.info("  /p/ link: %s | text: '%s'", l["href"], l["text"])

        other_links = [l for l in info["allLinks"] if "/p/" not in l["href"] and l["href"] and not l["href"].startswith("#")]
        logger.info("Other notable links (sample):")
        for l in other_links[:10]:
            logger.info("  href: %s | text: '%s'", l["href"], l["text"])

        logger.info("Body preview: %s", info["bodyPreview"][:300].replace("\n", " | "))

        try:
            nuxt = page.evaluate("""() => {
                try { return JSON.stringify(window.__NUXT__ || {}).slice(0, 2000); }
                catch(e) { return 'no __NUXT__'; }
            }""")
            if nuxt and nuxt != "no __NUXT__":
                logger.info("__NUXT__ found: %s...", nuxt[:300])
        except Exception:
            pass

        try:
            init = page.evaluate("""() => {
                try { return JSON.stringify(window.__INITIAL_STATE__ || {}).slice(0, 2000); }
                catch(e) { return 'no __INITIAL_STATE__'; }
            }""")
            if init and init != "no __INITIAL_STATE__":
                logger.info("__INITIAL_STATE__ found: %s...", init[:300])
        except Exception:
            pass

    except Exception as e:
        logger.warning("Enjoei: erro no diagnostico: %s", e)


def _extract_from_api(api_results: list) -> list[dict]:
    for entry in api_results:
        url = entry.get("url", "")
        if "graphql-search-x" not in url and "searchProducts" not in url:
            continue
        data = entry.get("data", {})
        try:
            products = data.get("data", {}).get("searchProductsForStore", {}).get("edges", [])
            if not products:
                products = data.get("data", {}).get("searchProducts", {}).get("edges", [])
            if not products:
                products = data.get("data", {}).get("products", [])
        except Exception:
            continue

        if not products:
            logger.info("Enjoei: API graphql respondeu mas sem produtos")
            continue

        logger.info("Enjoei: API graphql retornou %d produtos", len(products))
        items = []
        for edge in products[:20]:
            try:
                node = edge.get("node", edge)
                title = node.get("title", "")
                price_text = node.get("price", "")
                listing_url = node.get("url", "") or node.get("slug", "")
                seller = node.get("seller", {}).get("name", "") if isinstance(node.get("seller"), dict) else ""

                if not listing_url:
                    slug = node.get("slug", "")
                    if slug:
                        listing_url = f"https://www.enjoei.com.br/p/{slug}"

                if not title or not price_text:
                    continue

                if isinstance(price_text, (int, float)):
                    price_text = f"R$ {price_text:.2f}".replace(".", ",")

                items.append({
                    "title": title,
                    "price_text": str(price_text) if price_text else None,
                    "seller_name": seller or None,
                    "listing_url": listing_url or "",
                })
            except Exception as e:
                logger.debug("Enjoei: erro ao extrair item da API: %s", e)
                continue

        if items:
            logger.info("Enjoei: %d candidatos extraidos da API", len(items))
            return items

    return []


def _extract_from_page(page) -> list[dict]:
    logger.info("Enjoei: extraindo candidatos da pagina (via a[href*='/p/'])")

    links = page.query_selector_all("a[href*='/p/']")
    if not links:
        links = page.query_selector_all("a[href*='/produto/']")
    if not links:
        links = page.query_selector_all("a[href*='/item/']")

    if not links:
        logger.warning("Enjoei: nenhum link de produto encontrado com selectores conhecidos")
        return []

    logger.info("Enjoei: %d links de produto encontrados", len(links))

    seen = set()
    all_items = []

    for link in links[:30]:
        try:
            href = link.get_attribute("href")
            if not href:
                continue

            full_url = href if href.startswith("http") else "https://www.enjoei.com.br" + href

            if full_url in seen:
                continue
            seen.add(full_url)

            title = _extract_title(link, href)
            price_text = _extract_price(link, page)
            seller = _extract_seller(link)

            all_items.append({
                "title": title,
                "price_text": price_text,
                "seller_name": seller,
                "listing_url": full_url,
            })
        except Exception as e:
            logger.debug("Enjoei: erro ao extrair item: %s", e)
            continue

    logger.info("Enjoei: %d candidatos extraidos", len(all_items))

    if all_items:
        for item in all_items[:3]:
            logger.info("  exemplo: '%s' | preco='%s' | url='%s'",
                        item["title"], item["price_text"], item["listing_url"])

    return all_items


def _extract_title(link, href: str) -> str:
    text = link.text_content().strip() if link.text_content() else ""

    if text and len(text) > 3:
        return text

    match = re.search(r"/(?:p|produto|item)/(.+?)-(\d+)$", href)
    if match:
        slug = match.group(1)
        return slug.replace("-", " ").title()

    return text or ""


def _extract_price(link, page) -> str | None:
    parent = link.parent_element()
    if parent:
        candidates = parent.query_selector_all(
            "[class*='price'], [class*='Price'], [class*='value'], "
            "[class*='preco'], [class*='Preco'], [class*='currency'], "
            "[class*='amount'], [class*='Amount'], strong, span"
        )
        for el in candidates:
            text = el.text_content().strip() if el.text_content() else ""
            if re.search(r"R\$\s*[\d\.,]+", text):
                return text

    try:
        body_text = page.evaluate("document.body.innerText")
        match = re.search(r"R\$\s*[\d.,]+", body_text)
        if match:
            return match.group(0)
    except Exception:
        pass

    return None


def _extract_seller(link) -> str | None:
    parent = link.parent_element()
    for _ in range(3):
        if parent:
            candidates = parent.query_selector_all(
                "[class*='seller'], [class*='Seller'], [class*='author'], "
                "[class*='user'], [class*='vendedor'], small, [class*='caption']"
            )
            for el in candidates:
                text = el.text_content().strip() if el.text_content() else ""
                if text and len(text) < 60:
                    return text
            parent = parent.parent_element()
        else:
            break
    return None


def _extract_via_evaluate(page) -> list[dict]:
    logger.info("Enjoei: extraindo via page.evaluate()")
    try:
        items = page.evaluate("""() => {
            const cards = document.querySelectorAll('[class*="sc-"], [class*="card"], [class*="Card"], article, li[class]');
            const results = [];
            const seen = new Set();
            for (const card of cards) {
                const link = card.querySelector('a');
                const href = link ? (link.getAttribute('href') || '') : '';
                const text = card.textContent || '';
                if (!href && !text.trim()) continue;
                if (seen.has(text.slice(0, 100))) continue;
                seen.add(text.slice(0, 100));
                results.push({
                    href: href,
                    text: text.trim().slice(0, 200),
                    html: card.innerHTML.slice(0, 300)
                });
            }
            return results.slice(0, 30);
        }""")

        logger.info("Enjoei: evaluate retornou %d candidatos", len(items))
        if items:
            logger.info("  primeiro: href='%s' text='%s'", items[0]["href"], items[0]["text"])
            logger.info("  primeiro html: %s", items[0]["html"])

        parsed = []
        for item in items:
            href = item.get("href", "")
            text = item.get("text", "")
            full_url = href if href.startswith("http") else "https://www.enjoei.com.br" + href

            title_match = re.search(r"R\$\s*[\d.,]+", text)
            price_text = title_match.group(0) if title_match else None

            parsed.append({
                "title": text[:120] or _extract_title_from_href(href),
                "price_text": price_text,
                "seller_name": None,
                "listing_url": full_url,
            })
        return parsed
    except Exception as e:
        logger.warning("Enjoei: erro no evaluate: %s", e)
        return []


def _extract_title_from_href(href: str) -> str:
    if not href:
        return ""
    match = re.search(r"/(?:p|produto|item)/(.+?)-(\d+)$", href)
    if match:
        return match.group(1).replace("-", " ").title()
    return ""


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
    logger.info("Enjoei: melhor match (score=%.2f) entre %d candidatos: '%s'",
                best_score, len(candidates), best["title"])
    return best if best_score >= 0.15 else None


def search_enjoei(search_query: str, context) -> list[dict]:
    page = None
    try:
        page = context.new_page()
        page.set_default_timeout(45000)

        url = ENJOEI_URL.format(quote(search_query))
        logger.info("Enjoei: buscando '%s'", search_query)

        api_results = []
        def handle_response(response):
            nonlocal api_results
            rurl = response.url
            if any(x in rurl for x in ["/api/", "/search", "/listing", "/graphql"]):
                try:
                    ct = response.headers.get("content-type", "")
                    if "json" in ct:
                        data = response.json()
                        api_results.append({"url": rurl, "data": data})
                        logger.info("Enjoei: API response de %s (%d bytes)", rurl, len(str(data)))
                except Exception:
                    pass

        page.on("response", handle_response)

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        _log_diagnostics(page, search_query)

        try:
            page.wait_for_function(
                "() => document.querySelector('a[href*=\"/p/\"]') || "
                "document.querySelector('[class*=\"sc-\"]') || "
                "document.body.innerText.includes('R$')",
                timeout=15000
            )
            logger.info("Enjoei: pagina parece ter conteudo carregado")
        except Exception:
            logger.warning("Enjoei: timeout esperando conteudo renderizar")

        page.wait_for_timeout(1000)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        _dump_html(page, search_query)

        if api_results:
            logger.info("Enjoei: %d respostas de API capturadas", len(api_results))
            for r in api_results[:5]:
                data_preview = str(r.get("data", {}))[:200]
                logger.info("  API: %s => %s...", r["url"], data_preview)

        candidates = _extract_from_api(api_results)

        if not candidates:
            logger.info("Enjoei: extracao por API falhou, tentando DOM")
            candidates = _extract_from_page(page)

        if not candidates:
            logger.info("Enjoei: extracao por selector falhou, tentando page.evaluate")
            candidates = _extract_via_evaluate(page)

        if not candidates:
            logger.warning("Enjoei: nenhum candidato encontrado para '%s'", search_query)
            return []

        expected = search_query.replace(" cd original", "").replace(" cd", "")
        best = _best_match(candidates, expected, search_query)
        return [best] if best else []

    except Exception as e:
        logger.error("Enjoei: erro na busca '%s': %s", search_query, e)
        return []
    finally:
        if page:
            page.close()
