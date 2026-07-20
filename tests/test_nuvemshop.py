import pytest
from bs4 import BeautifulSoup
from scraper.nuvemshop import _extract_from_html


BASE_URL = "https://www.fonoteca.com.br"


class TestExtractFromHtml:
    def test_jsonld_single_product(self):
        html = """
        <html><body>
        <script type="application/ld+json">
        {"@type": "Product", "name": "CD Thriller Michael Jackson", "offers": {"price": "49.90"}, "url": "https://www.fonoteca.com.br/produtos/thriller"}
        </script>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert len(items) == 1
        assert items[0]["title"] == "CD Thriller Michael Jackson"
        assert items[0]["price_text"] == "R$ 49.90"
        assert items[0]["listing_url"] == "https://www.fonoteca.com.br/produtos/thriller"

    def test_jsonld_multiple_products(self):
        html = """
        <html><body>
        <script type="application/ld+json">
        [{"@type": "Product", "name": "CD A", "offers": {"price": "10"}, "url": "https://example.com/a"},
         {"@type": "Product", "name": "CD B", "offers": {"price": "20"}, "url": "https://example.com/b"}]
        </script>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert len(items) == 2
        assert items[0]["title"] == "CD A"
        assert items[1]["title"] == "CD B"

    def test_jsonld_offers_list(self):
        html = """
        <html><body>
        <script type="application/ld+json">
        {"@type": "Product", "name": "CD Test", "offers": [{"price": "99.90"}], "url": "https://example.com/test"}
        </script>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert len(items) == 1
        assert items[0]["price_text"] == "R$ 99.90"

    def test_jsonld_skip_non_product(self):
        html = """
        <html><body>
        <script type="application/ld+json">
        {"@type": "WebSite", "name": "Fonoteca"}
        </script>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert items == []

    def test_jsonld_image_string(self):
        html = """
        <html><body>
        <script type="application/ld+json">
        {"@type": "Product", "name": "CD Cover", "image": "https://example.com/cover.jpg", "offers": {"price": "29.90"}, "url": "https://example.com/cd"}
        </script>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert len(items) == 1

    def test_containers_div_product(self):
        html = """
        <html><body>
        <div class="js-item-product">
            <h2 class="product-name">CD Thriller</h2>
            <span class="price">R$ 49,90</span>
            <a href="/produtos/thriller">ver</a>
        </div>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert len(items) == 1
        assert items[0]["title"] == "CD Thriller"

    def test_containers_li_product(self):
        html = """
        <html><body>
        <li class="product">
            <h3>CD Abbey Road</h3>
            <span class="preco">R$ 39,90</span>
        </li>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert len(items) == 1

    def test_containers_a_tag_fallback(self):
        html = """
        <html><body>
        <a href="/produtos/thriller" title="CD Thriller Michael Jackson">CD Thriller Michael Jackson</a>
        <a href="/produtos/abbey" title="CD Abbey Road">CD Abbey Road</a>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert len(items) == 2

    def test_empty_html(self):
        soup = BeautifulSoup("", "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert items == []

    def test_no_product_elements(self):
        html = "<html><body><p>nada aqui</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        items = _extract_from_html(soup, BASE_URL)
        assert items == []
