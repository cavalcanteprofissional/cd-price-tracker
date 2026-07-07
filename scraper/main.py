import logging
import os
import sys
import time
import traceback
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

# Carrega .env da pasta scraper/ antes de qualquer import que leia env vars
load_dotenv(Path(__file__).parent / ".env")

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from tenacity import retry, stop_after_attempt, wait_exponential

from scraper.alert import send_alert
from scraper.amazon import scrape_amazon, search_amazon
from scraper.amazon_global import search_amazon_marketplace, MARKETPLACES
from scraper.enjoei import search_enjoei
from scraper.filter import is_suspected_fanmade
from scraper.magalu import search_magalu
from scraper.mercadolivre import scrape_mercadolivre, try_mercadolivre_api
from scraper.models import ScrapeResult, ScrapedProduct
from scraper.price_parser import parse_br_price
from scraper.shopee import scrape_shopee
from scraper.supabase_client import supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def auto_search_query(title: str, artist: str) -> str:
    return f"{title} {artist} cd original"


def persist_result(result: ScrapeResult):
    if result.status == "success" and result.product:
        supabase.table("price_history").insert({
            "product_platform_config_id": result.config_id,
            "price": float(result.product.price),
            "currency": result.product.currency,
            "availability": result.product.availability,
            "seller_name": result.product.seller_name,
            "listing_url": result.product.listing_url,
        }).execute()

    supabase.table("scrape_log").insert({
        "product_platform_config_id": result.config_id,
        "status": result.status,
        "raw_title": result.raw_title,
        "detail": result.detail,
    }).execute()


def choose_lowest_price(items: list[dict]) -> dict | None:
    if not items:
        return None
    return min(items, key=lambda x: parse_br_price(x["price_text"]))


BASE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

ANTI_DETECT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {} };
"""


def _make_stealth_context(browser):
    context = browser.new_context(
        user_agent=BASE_USER_AGENT,
        viewport={"width": 1366, "height": 768},
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        geolocation={"latitude": -23.5505, "longitude": -46.6333},
        permissions=["geolocation"],
    )
    Stealth().apply_stealth_sync(context)
    context.add_init_script(ANTI_DETECT_SCRIPT)
    return context


def _process_platform_scrape(
    platform: str,
    config: dict,
    scrape_fn,
    search_query: str | None = None,
) -> ScrapeResult:
    if not search_query:
        title = config["products"]["title"]
        artist = config["products"]["artist"]
        search_query = auto_search_query(title, artist)
        logger.info("%s: search_query auto-gerado: '%s'", platform, search_query)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = _make_stealth_context(browser)
        try:
            results = scrape_fn(search_query, context)
            if not results:
                return ScrapeResult(config["id"], config["product_id"], "not_found", None, None, "sem resultados")

            valid = []
            for item in results:
                if is_suspected_fanmade(item["title"]):
                    supabase.table("scrape_log").insert({
                        "product_platform_config_id": config["id"],
                        "status": "skipped_fanmade",
                        "raw_title": item["title"],
                        "detail": None,
                    }).execute()
                else:
                    valid.append(item)

            if not valid:
                return ScrapeResult(config["id"], config["product_id"], "not_found", None, None, "tudo filtrado como fanmade")

            best = choose_lowest_price(valid)
            product = ScrapedProduct(
                title=best["title"],
                price=Decimal(str(parse_br_price(best["price_text"]))),
                currency="BRL",
                availability="in_stock",
                seller_name=best.get("seller_name"),
                listing_url=best["listing_url"],
                platform=platform,
            )
            return ScrapeResult(config["id"], config["product_id"], "success", product, best["title"], None)
        finally:
            browser.close()


def process_amazon(config: dict) -> ScrapeResult:
    amazon_url = config.get("amazon_url")
    title = config["products"]["title"]
    artist = config["products"]["artist"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = _make_stealth_context(browser)
        try:
            if amazon_url:
                data = scrape_amazon(amazon_url, context)
            else:
                logger.info("Amazon: amazon_url vazio, buscando '%s - %s'", artist, title)
                data = search_amazon(title, artist, context)

            if not data:
                return ScrapeResult(config["id"], config["product_id"], "error", None, None, "falha ao extrair dados")

            if is_suspected_fanmade(data["title"]):
                return ScrapeResult(config["id"], config["product_id"], "skipped_fanmade", None, data["title"], None)

            product = ScrapedProduct(
                title=data["title"],
                price=Decimal(str(parse_br_price(data["price_text"]))),
                currency="BRL",
                availability=data["availability"],
                seller_name=data["seller_name"],
                listing_url=data["listing_url"],
                platform="amazon",
            )
            return ScrapeResult(config["id"], config["product_id"], "success", product, data["title"], None)
        finally:
            browser.close()


def process_amazon_global(platform: str, config: dict) -> ScrapeResult:
    title = config["products"]["title"]
    artist = config["products"]["artist"]
    cfg = MARKETPLACES.get(platform)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = _make_stealth_context(browser)
        try:
            logger.info("%s: buscando '%s - %s'", platform, artist, title)
            data = search_amazon_marketplace(title, artist, context, platform)

            if not data:
                return ScrapeResult(config["id"], config["product_id"], "error", None, None, "falha ao extrair dados")

            if is_suspected_fanmade(data["title"]):
                return ScrapeResult(config["id"], config["product_id"], "skipped_fanmade", None, data["title"], None)

            price_text = data["price_text"]
            currency = data.get("currency", "USD")

            product = ScrapedProduct(
                title=data["title"],
                price=Decimal(str(parse_br_price(price_text))),
                currency=currency,
                availability=data["availability"],
                seller_name=data["seller_name"],
                listing_url=data["listing_url"],
                platform=platform,
            )
            return ScrapeResult(config["id"], config["product_id"], "success", product, data["title"], None)
        finally:
            browser.close()


def process_mercadolivre(config: dict) -> ScrapeResult:
    search_query = config.get("search_query")
    title = config["products"]["title"]
    artist = config["products"]["artist"]
    if not search_query:
        search_query = auto_search_query(title, artist)

    # 1. Tentar API oficial (httpx, sem browser)
    api_results = try_mercadolivre_api(search_query)
    if api_results is not None:
        config_id = config["id"]
        product_id = config["product_id"]

        valid = []
        for item in api_results:
            if is_suspected_fanmade(item["title"]):
                supabase.table("scrape_log").insert({
                    "product_platform_config_id": config_id,
                    "status": "skipped_fanmade",
                    "raw_title": item["title"],
                    "detail": None,
                }).execute()
            else:
                valid.append(item)

        if valid:
            best = choose_lowest_price(valid)
            product = ScrapedProduct(
                title=best["title"],
                price=Decimal(str(parse_br_price(best["price_text"]))),
                currency="BRL",
                availability="in_stock",
                seller_name=best.get("seller_name"),
                listing_url=best["listing_url"],
                platform="mercado_livre",
            )
            logger.info("ML: sucesso via API oficial — %s R$ %s", best["title"], best["price_text"])
            return ScrapeResult(config_id, product_id, "success", product, best["title"], None)
        else:
            return ScrapeResult(config_id, product_id, "not_found", None, None, "tudo filtrado como fanmade")

    # 2. Fallback: Playwright (com browser)
    return _process_platform_scrape("mercado_livre", config, scrape_mercadolivre, search_query)


def process_magalu(config: dict) -> ScrapeResult:
    search_query = config.get("search_query")
    return _process_platform_scrape("magalu", config, search_magalu, search_query)


def process_shopee(config: dict) -> ScrapeResult:
    search_query = config.get("search_query")
    return _process_platform_scrape("shopee", config, scrape_shopee, search_query)


def process_enjoei(config: dict) -> ScrapeResult:
    search_query = config.get("search_query")
    return _process_platform_scrape("enjoei", config, search_enjoei, search_query)


def send_digest():
    try:
        from scraper.email_digest import send_digest_emails
        send_digest_emails()
    except Exception as e:
        logger.error("Falha ao enviar digest: %s", e)


def main():
    logger.info("Iniciando pipeline semanal de scraping")

    configs = supabase.table("product_platform_config") \
        .select("*, products!inner(*)") \
        .eq("active", True) \
        .execute()

    logger.info("Encontradas %d configuracoes ativas", len(configs.data))

    stats = {"success": 0, "error": 0, "skipped_fanmade": 0, "not_found": 0}

    for cfg in configs.data:
        platform = cfg["platform"]
        logger.info("Processando %s (product_id=%s)", platform, cfg["product_id"])

        try:
            if platform == "amazon":
                result = process_amazon(cfg)
            elif platform in ("amazon_us", "amazon_uk", "amazon_de"):
                result = process_amazon_global(platform, cfg)
            elif platform == "mercado_livre":
                result = process_mercadolivre(cfg)
            elif platform == "magalu":
                result = process_magalu(cfg)
            elif platform == "shopee":
                result = process_shopee(cfg)
            elif platform == "enjoei":
                result = process_enjoei(cfg)
            elif platform in ("americanas", "casas_bahia", "submarino", "carrefour", "extra"):
                logger.warning("Scraper nao implementado para: %s", platform)
                continue
            else:
                logger.warning("Plataforma desconhecida: %s", platform)
                continue

            persist_result(result)
            stats[result.status] = stats.get(result.status, 0) + 1
        except Exception as e:
            logger.error("Erro ao processar %s/%s: %s", cfg["product_id"], platform, e)
            persist_result(ScrapeResult(cfg["id"], cfg["product_id"], "error", None, None, str(e)))
            stats["error"] += 1

        time.sleep(1)

    logger.info("Pipeline concluido. Stats: %s", stats)

    send_digest()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        error_msg = traceback.format_exc()
        logger.critical("Falha fatal no pipeline: %s", error_msg)
        try:
            send_alert(f"Pipeline semanal falhou:\n\n{error_msg}")
        except Exception:
            logger.critical("Falha tambem ao enviar alerta")
        sys.exit(1)
