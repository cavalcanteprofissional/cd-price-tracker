import pytest
from scraper.mercadolivre import scrape_mercadolivre, _extract_from_api_public


@pytest.fixture(autouse=True)
def _no_sleep(mocker):
    mocker.patch("scraper.mercadolivre.time.sleep")


class TestExtractFromApiPublic:
    def test_success(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {"title": "CD Thriller Michael Jackson Original", "price": 79.90, "permalink": "https://mercadolivre.com.br/produto/123", "seller": {"nickname": "Vendedor XYZ"}},
                {"title": "CD Thriller Edicao Especial", "price": 99.90, "permalink": "https://mercadolivre.com.br/produto/456"},
            ]
        }
        mocker.patch("scraper.mercadolivre.httpx.get", return_value=mock_resp)

        results = _extract_from_api_public("Thriller Michael Jackson")
        assert results is not None
        assert len(results) == 2
        assert results[0]["title"] == "CD Thriller Michael Jackson Original"
        assert results[0]["seller_name"] == "Vendedor XYZ"
        assert results[1]["seller_name"] is None

    def test_empty_results(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = {"results": []}
        mocker.patch("scraper.mercadolivre.httpx.get", return_value=mock_resp)

        results = _extract_from_api_public("nonexistent")
        assert results is None

    def test_skip_missing_title(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {"price": 50.00, "permalink": "https://mercadolivre.com.br/p/1"},
                {"title": "CD Valido", "price": 30.00, "permalink": "https://mercadolivre.com.br/p/2"},
            ]
        }
        mocker.patch("scraper.mercadolivre.httpx.get", return_value=mock_resp)

        results = _extract_from_api_public("test")
        assert results is not None
        assert len(results) == 1
        assert results[0]["title"] == "CD Valido"

    def test_exception_returns_none(self, mocker):
        mocker.patch("scraper.mercadolivre.httpx.get", side_effect=Exception("API error"))

        results = _extract_from_api_public("test")
        assert results is None


class TestScrapeMercadoLivre:
    def test_success(self, mocker):
        mock_item = mocker.MagicMock()

        mock_title = mocker.MagicMock()
        mock_title.text_content.return_value = "CD Thriller - Michael Jackson Original Lacrado"
        mock_price = mocker.MagicMock()
        mock_price.text_content.return_value = "79,90"
        mock_seller = mocker.MagicMock()
        mock_seller.text_content.return_value = "Vendedor XYZ"
        mock_link = mocker.MagicMock()
        mock_link.get_attribute.return_value = "https://www.mercadolivre.com.br/produto/123"

        mock_item.query_selector.side_effect = lambda sel: {
            ".ui-search-item__title": mock_title,
            ".andes-money-amount__fraction": mock_price,
            ".ui-search-item__seller-info": mock_seller,
            "a.ui-search-link": mock_link,
        }.get(sel)

        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = [mock_item, mock_item]
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = scrape_mercadolivre("Thriller Michael Jackson cd original", mock_context)
        assert len(results) == 2
        assert results[0]["title"] == "CD Thriller - Michael Jackson Original Lacrado"
        assert results[0]["price_text"] == "79,90"
        assert results[0]["seller_name"] == "Vendedor XYZ"
        assert results[0]["listing_url"] == "https://www.mercadolivre.com.br/produto/123"

    def test_no_results(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = []
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = scrape_mercadolivre("zzzzznonexistent", mock_context)
        assert results == []

    def test_relative_url_resolved(self, mocker):
        mock_item = mocker.MagicMock()

        mock_title = mocker.MagicMock()
        mock_title.text_content.return_value = "CD Teste"
        mock_price = mocker.MagicMock()
        mock_price.text_content.return_value = "50,00"
        mock_link = mocker.MagicMock()
        mock_link.get_attribute.return_value = "/produto/456"

        mock_item.query_selector.side_effect = lambda sel: {
            ".ui-search-item__title": mock_title,
            ".andes-money-amount__fraction": mock_price,
            "a.ui-search-link": mock_link,
        }.get(sel)

        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = [mock_item]
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = scrape_mercadolivre("teste", mock_context)
        assert results[0]["listing_url"].startswith("https://")

    def test_skip_missing_title(self, mocker):
        mock_item = mocker.MagicMock()
        mock_item.query_selector.return_value = None

        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = [mock_item]
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = scrape_mercadolivre("teste", mock_context)
        assert results == []

    def test_exception_returns_empty(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.goto.side_effect = Exception("Network error")
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = scrape_mercadolivre("teste", mock_context)
        assert results == []
