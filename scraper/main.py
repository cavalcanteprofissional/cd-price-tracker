import logging
import os
import sys
import time
import traceback
from decimal import Decimal

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from tenacity import retry, stop_after_attempt, wait_exponential

from scraper.alert import send_alert
from scraper.amazon import scrape_amazon
from scraper.filter import is_suspected_fanmade
from scraper.mercadolivre import scrape_mercadolivre
from scraper.models import ScrapeResult, ScrapedProduct
from scraper.price_parser import parse_br_price
from scraper.shopee import scrape_shopee
from scraper.supabase_client import supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


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


def process_amazon(config: dict) -> ScrapeResult:
    amazon_url = config["amazon_url"]
    if not amazon_url:
        return ScrapeResult(config["id"], config["product_id"], "error", None, None, "amazon_url vazio")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        stealth_sync(context)
        try:
            data = scrape_amazon(amazon_url, context)
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


def process_mercadolivre(config: dict) -> ScrapeResult:
    search_query = config["search_query"]
    if not search_query:
        return ScrapeResult(config["id"], config["product_id"], "error", None, None, "search_query vazio")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        try:
            results = scrape_mercadolivre(search_query, context)
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
                platform="mercado_livre",
            )
            return ScrapeResult(config["id"], config["product_id"], "success", product, best["title"], None)
        finally:
            browser.close()


def process_shopee(config: dict) -> ScrapeResult:
    search_query = config["search_query"]
    if not search_query:
        return ScrapeResult(config["id"], config["product_id"], "error", None, None, "search_query vazio")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        try:
            results = scrape_shopee(search_query, context)
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
                platform="shopee",
            )
            return ScrapeResult(config["id"], config["product_id"], "success", product, best["title"], None)
        finally:
            browser.close()


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
            elif platform == "mercado_livre":
                result = process_mercadolivre(cfg)
            elif platform == "shopee":
                result = process_shopee(cfg)
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
