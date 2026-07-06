import pytest
from scraper.price_parser import parse_br_price


@pytest.mark.parametrize("text,expected", [
    ("R$ 49,90", 49.90),
    ("R$ 1.234,56", 1234.56),
    ("29,99", 29.99),
    ("  R$ 5,00  ", 5.0),
    ("R$ 100", 100.0),
    ("R$ 0,50", 0.50),
    ("R$1.000,00", 1000.00),
    ("10.000,00", 10000.00),
    ("R$ 99", 99.0),
    ("0,99", 0.99),
])
def test_parse_br_price(text, expected):
    assert parse_br_price(text) == expected
