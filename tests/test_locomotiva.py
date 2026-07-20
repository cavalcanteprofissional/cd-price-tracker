import pytest


class TestSearchLocomotiva:
    def test_success(self, mocker):
        html = """
        <html><body>
        <div class="product-item-container">
            <div class="iluria-layout-search-product-title">
                <a href="/cd-thriller">CD Thriller Michael Jackson Original</a>
            </div>
            <span class="product-price-currency">R$</span>
            <span class="product-price-text">49,90</span>
        </div>
        <div class="product-item-container">
            <div class="iluria-layout-search-product-title">
                <a href="/cd-abbey-road">CD Abbey Road Beatles</a>
            </div>
            <span class="product-price-currency">R$</span>
            <span class="product-price-text">39,90</span>
        </div>
        </body></html>
        """
        mock_resp = mocker.MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = html
        mocker.patch("scraper.locomotiva.httpx.get", return_value=mock_resp)

        from scraper.locomotiva import search_locomotiva
        items = search_locomotiva("Thriller")
        assert len(items) == 2
        assert items[0]["title"] == "CD Thriller Michael Jackson Original"
        assert items[0]["listing_url"] == "https://www.locomotivadiscos.com.br/cd-thriller"

    def test_empty_results(self, mocker):
        html = "<html><body><p>sem produtos</p></body></html>"
        mock_resp = mocker.MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = html
        mocker.patch("scraper.locomotiva.httpx.get", return_value=mock_resp)

        from scraper.locomotiva import search_locomotiva
        items = search_locomotiva("nonexistent")
        assert items == []

    def test_http_error(self, mocker):
        mocker.patch("scraper.locomotiva.httpx.get", side_effect=Exception("HTTP error"))

        from scraper.locomotiva import search_locomotiva
        items = search_locomotiva("error")
        assert items == []
