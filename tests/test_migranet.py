import pytest


class TestSearchMigranet:
    def test_success(self, mocker):
        html = """
        <html><body>
        <div class="listagem-item">
            <a class="nome-produto" href="/produto/thriller">CD Thriller Michael Jackson</a>
            <strong class="preco-promocional" data-sell-price="49.90">R$ 49,90</strong>
        </div>
        <div class="listagem-item">
            <a class="nome-produto" href="/produto/abbey-road">CD Abbey Road Beatles</a>
            <strong class="preco-promocional" data-sell-price="39.90">R$ 39,90</strong>
        </div>
        </body></html>
        """
        mock_resp = mocker.MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = html
        mocker.patch("scraper.migranet.httpx.get", return_value=mock_resp)

        from scraper.migranet import search_migranet
        items = search_migranet("Thriller")
        assert len(items) == 2
        assert items[0]["title"] == "CD Thriller Michael Jackson"
        assert "49.90" in items[0]["price_text"]

    def test_empty_results(self, mocker):
        html = "<html><body><p>sem produtos</p></body></html>"
        mock_resp = mocker.MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = html
        mocker.patch("scraper.migranet.httpx.get", return_value=mock_resp)

        from scraper.migranet import search_migranet
        items = search_migranet("nonexistent")
        assert items == []

    def test_http_error(self, mocker):
        mocker.patch("scraper.migranet.httpx.get", side_effect=Exception("HTTP error"))

        from scraper.migranet import search_migranet
        items = search_migranet("error")
        assert items == []

    def test_no_title_element(self, mocker):
        html = """
        <html><body>
        <div class="listagem-item">
            <span>sem link de produto</span>
        </div>
        </body></html>
        """
        mock_resp = mocker.MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = html
        mocker.patch("scraper.migranet.httpx.get", return_value=mock_resp)

        from scraper.migranet import search_migranet
        items = search_migranet("test")
        assert items == []

    def test_price_without_data_attribute(self, mocker):
        html = """
        <html><body>
        <div class="listagem-item">
            <a class="nome-produto" href="/produto/test">CD Test</a>
            <strong class="preco-promocional">R$ 29,90</strong>
        </div>
        </body></html>
        """
        mock_resp = mocker.MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = html
        mocker.patch("scraper.migranet.httpx.get", return_value=mock_resp)

        from scraper.migranet import search_migranet
        items = search_migranet("test")
        assert len(items) == 1
        assert "29,90" in items[0]["price_text"]
