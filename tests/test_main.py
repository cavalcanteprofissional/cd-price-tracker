import pytest
from decimal import Decimal
from scraper.main import auto_search_query, choose_lowest_price, persist_result
from scraper.models import ScrapeResult, ScrapedProduct


class TestAutoSearchQuery:
    def test_basic(self):
        assert auto_search_query("Thriller", "Michael Jackson") == "Thriller Michael Jackson cd original"

    def test_special_chars(self):
        assert auto_search_query("The Dark Side of the Moon", "Pink Floyd") == "The Dark Side of the Moon Pink Floyd cd original"


class TestChooseLowestPrice:
    def test_multiple(self):
        items = [
            {"price_text": "R$ 99,90"},
            {"price_text": "R$ 49,90"},
            {"price_text": "R$ 79,90"},
        ]
        best = choose_lowest_price(items)
        assert best == items[1]

    def test_single(self):
        items = [{"price_text": "R$ 59,90"}]
        assert choose_lowest_price(items) == items[0]

    def test_empty(self):
        assert choose_lowest_price([]) is None

    def test_large_numbers(self):
        items = [
            {"price_text": "R$ 1.234,56"},
            {"price_text": "R$ 999,99"},
        ]
        best = choose_lowest_price(items)
        assert best == items[1]


class TestPersistResult:
    def test_success_persists_price_and_log(self, mocker):
        mock_supabase = mocker.patch("scraper.main.supabase")
        product = ScrapedProduct(
            title="Thriller",
            price=Decimal("49.90"),
            currency="BRL",
            availability="in_stock",
            seller_name="Vendedor",
            listing_url="https://amazon.com.br/dp/123",
            platform="amazon",
        )
        result = ScrapeResult(
            config_id="cfg-1",
            product_id="prod-1",
            status="success",
            product=product,
            raw_title="Thriller - Michael Jackson",
            detail=None,
        )

        persist_result(result)

        price_calls = [args[0] for args in mock_supabase.table.call_args_list if args[0][0] == "price_history"]
        log_calls = [args[0] for args in mock_supabase.table.call_args_list if args[0][0] == "scrape_log"]
        assert len(price_calls) == 1
        assert len(log_calls) == 1

    def test_error_persists_only_log(self, mocker):
        mock_supabase = mocker.patch("scraper.main.supabase")
        result = ScrapeResult(
            config_id="cfg-1",
            product_id="prod-1",
            status="error",
            product=None,
            raw_title=None,
            detail="falha ao extrair dados",
        )

        persist_result(result)

        price_calls = [args[0] for args in mock_supabase.table.call_args_list if args[0][0] == "price_history"]
        log_calls = [args[0] for args in mock_supabase.table.call_args_list if args[0][0] == "scrape_log"]
        assert len(price_calls) == 0
        assert len(log_calls) == 1
