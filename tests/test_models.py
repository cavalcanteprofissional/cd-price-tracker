from decimal import Decimal
from scraper.models import ScrapedProduct, ScrapeResult


class TestScrapedProduct:
    def test_full_creation(self):
        p = ScrapedProduct(
            title="Thriller",
            price=Decimal("49.90"),
            currency="BRL",
            availability="in_stock",
            seller_name="Amazon",
            listing_url="https://amazon.com.br/dp/123",
            platform="amazon",
        )
        assert p.title == "Thriller"
        assert p.price == Decimal("49.90")
        assert p.currency == "BRL"

    def test_seller_none(self):
        p = ScrapedProduct(
            title="Test",
            price=Decimal("10.00"),
            currency="BRL",
            availability="in_stock",
            seller_name=None,
            listing_url="https://example.com",
            platform="shopee",
        )
        assert p.seller_name is None

    def test_decimal_precision(self):
        p = ScrapedProduct(
            title="Test",
            price=Decimal("1234.56"),
            currency="BRL",
            availability="in_stock",
            seller_name=None,
            listing_url="https://example.com",
            platform="mercado_livre",
        )
        assert p.price == Decimal("1234.56")


class TestScrapeResult:
    def test_success_result(self):
        product = ScrapedProduct(
            title="Thriller",
            price=Decimal("49.90"),
            currency="BRL",
            availability="in_stock",
            seller_name=None,
            listing_url="https://amazon.com.br/dp/123",
            platform="amazon",
        )
        r = ScrapeResult(
            config_id="cfg-1",
            product_id="prod-1",
            status="success",
            product=product,
            raw_title="Thriller - Michael Jackson",
            detail=None,
        )
        assert r.status == "success"
        assert r.product is not None
        assert r.product.price == Decimal("49.90")

    def test_error_result(self):
        r = ScrapeResult(
            config_id="cfg-1",
            product_id="prod-1",
            status="error",
            product=None,
            raw_title=None,
            detail="Timeout",
        )
        assert r.status == "error"
        assert r.product is None
        assert r.detail == "Timeout"

    def test_skipped_fanmade(self):
        r = ScrapeResult(
            config_id="cfg-1",
            product_id="prod-1",
            status="skipped_fanmade",
            product=None,
            raw_title="CD Fan Made",
            detail=None,
        )
        assert r.status == "skipped_fanmade"
        assert r.raw_title == "CD Fan Made"
