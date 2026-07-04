import pytest
from scraper.price_parser import parse_br_price


def test_simple():
    assert parse_br_price("R$ 49,90") == 49.90


def test_thousands():
    assert parse_br_price("R$ 1.234,56") == 1234.56


def test_no_symbol():
    assert parse_br_price("29,99") == 29.99


def test_whitespace():
    assert parse_br_price("  R$ 5,00  ") == 5.0


def test_integer():
    assert parse_br_price("R$ 100") == 100.0
