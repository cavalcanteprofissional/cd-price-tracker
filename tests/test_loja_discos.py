import pytest
from scraper.loja_discos import _parse_products


class TestParseProducts:
    def test_a_tags_direct(self):
        html = """
        <html><body>
        <a href="/produto/thriller">CD Thriller Michael Jackson Original</a>
        <a href="/produto/abbey-road">CD Abbey Road Beatles</a>
        </body></html>
        """
        items = _parse_products(html)
        assert len(items) == 2
        assert items[0]["title"] == "CD Thriller Michael Jackson Original"
        assert items[1]["title"] == "CD Abbey Road Beatles"

    def test_div_containers_with_price(self):
        html = """
        <html><body>
        <div class="produto">
            <h2>CD Thriller</h2>
            <span>por: R$ 49,90</span>
        </div>
        <div class="produto">
            <h2>CD Abbey Road</h2>
            <span>por: R$ 39,90</span>
        </div>
        </body></html>
        """
        items = _parse_products(html)
        assert len(items) == 2
        assert "49,90" in items[0]["price_text"]
        assert "39,90" in items[1]["price_text"]

    def test_div_without_price(self):
        html = """
        <html><body>
        <div class="produto">
            <h2>CD Sem Preco</h2>
        </div>
        </body></html>
        """
        items = _parse_products(html)
        assert len(items) == 1
        assert items[0]["price_text"] == ""

    def test_empty_html(self):
        items = _parse_products("")
        assert items == []

    def test_no_containers(self):
        html = "<html><body><p>nenhum produto aqui</p></body></html>"
        items = _parse_products(html)
        assert items == []

    def test_div_product_class(self):
        html = """
        <html><body>
        <div class="product">
            <h3 class="nome-produto">CD Dark Side</h3>
            <div class="preco">R$ 59,90</div>
        </div>
        </body></html>
        """
        items = _parse_products(html)
        assert len(items) == 1
        assert items[0]["title"] == "CD Dark Side"

    def test_url_resolved(self):
        html = """
        <html><body>
        <a href="/cd/thriller">CD Thriller</a>
        </body></html>
        """
        items = _parse_products(html)
        assert len(items) == 1
        assert items[0]["listing_url"].startswith("https://www.alojadediscos.com.br")

    def test_duplicates_skipped(self):
        html = """
        <html><body>
        <div class="produto"><h2>CD Thriller</h2><span>R$ 49,90</span></div>
        <div class="produto"><h2>CD Thriller</h2><span>R$ 49,90</span></div>
        </body></html>
        """
        items = _parse_products(html)
        assert len(items) == 1
