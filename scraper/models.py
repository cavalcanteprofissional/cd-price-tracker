from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ScrapedProduct:
    title: str
    price: Decimal
    currency: str
    availability: str
    seller_name: str | None
    listing_url: str
    platform: str


@dataclass
class ScrapeResult:
    config_id: str
    product_id: str
    status: str
    product: ScrapedProduct | None
    raw_title: str | None
    detail: str | None
