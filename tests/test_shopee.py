import pytest
from scraper.shopee import _extract_from_api, _extract_from_page, scrape_shopee


@pytest.fixture(autouse=True)
def _no_sleep(mocker):
    mocker.patch("scraper.shopee.time.sleep")


class TestExtractFromApi:
    def test_success(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = {
            "items": [
                {
                    "item_basic": {
                        "name": "CD Thriller Michael Jackson Original",
                        "price": 4990000,
                        "shopid": 12345,
                        "itemid": 67890,
                    }
                },
                {
                    "item_basic": {
                        "name": "CD Abbey Road Beatles",
                        "price": 3990000,
                        "shopid": 54321,
                        "itemid": 98765,
                    }
                }
            ]
        }
        mocker.patch("scraper.shopee.httpx.get", return_value=mock_resp)

        results = _extract_from_api("Thriller Michael Jackson cd original")
        assert results is not None
        assert len(results) == 2
        assert results[0]["price_text"] == "49.90"
        assert results[1]["price_text"] == "39.90"
        assert "shopee.com.br" in results[0]["listing_url"]

    def test_empty_items(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = {"items": []}
        mocker.patch("scraper.shopee.httpx.get", return_value=mock_resp)

        results = _extract_from_api("nonexistent")
        assert results is None

    def test_missing_item_basic(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = {"items": [{"no_basic": True}]}
        mocker.patch("scraper.shopee.httpx.get", return_value=mock_resp)

        results = _extract_from_api("test")
        assert results is not None
        assert len(results) == 0

    def test_api_error_returns_none(self, mocker):
        mocker.patch("scraper.shopee.httpx.get", side_effect=Exception("API error"))

        results = _extract_from_api("test")
        assert results is None


class TestExtractFromPage:
    def test_success(self, mocker):
        mock_item = mocker.MagicMock()

        mock_title = mocker.MagicMock()
        mock_title.text_content.return_value = "CD Thriller Original"
        mock_price = mocker.MagicMock()
        mock_price.text_content.return_value = "R$ 59,90"
        mock_link = mocker.MagicMock()
        mock_link.get_attribute.return_value = "https://shopee.com.br/product/1/2"

        mock_item.query_selector.side_effect = lambda sel: {
            "div[data-sqe='name']": mock_title,
            "span[data-sqe='price']": mock_price,
            "a[data-sqe='link']": mock_link,
        }.get(sel)

        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = [mock_item]
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = _extract_from_page("Thriller", mock_context)
        assert len(results) == 1
        assert results[0]["title"] == "CD Thriller Original"

    def test_no_results(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = []
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = _extract_from_page("nonexistent", mock_context)
        assert results == []

    def test_relative_url_resolved(self, mocker):
        mock_item = mocker.MagicMock()

        mock_title = mocker.MagicMock()
        mock_title.text_content.return_value = "CD Test"
        mock_price = mocker.MagicMock()
        mock_price.text_content.return_value = "30,00"
        mock_link = mocker.MagicMock()
        mock_link.get_attribute.return_value = "/product/3/4"

        mock_item.query_selector.side_effect = lambda sel: {
            "div[data-sqe='name']": mock_title,
            "span[data-sqe='price']": mock_price,
            "a[data-sqe='link']": mock_link,
        }.get(sel)

        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = [mock_item]
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = _extract_from_page("test", mock_context)
        assert results[0]["listing_url"].startswith("https://shopee.com.br")

    def test_exception_returns_empty(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.goto.side_effect = Exception("Error")
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        results = _extract_from_page("test", mock_context)
        assert results == []


class TestScrapeShopee:
    def test_uses_api_first(self, mocker):
        mocker.patch("scraper.shopee._extract_from_api", return_value=[{"title": "CD Test", "price_text": "49.90"}])
        mocker.patch("scraper.shopee._extract_from_page")

        results = scrape_shopee("test", mocker.MagicMock())
        assert len(results) == 1

    def test_fallback_to_page(self, mocker):
        mocker.patch("scraper.shopee._extract_from_api", return_value=None)
        mocker.patch("scraper.shopee._extract_from_page", return_value=[{"title": "CD Test"}])

        results = scrape_shopee("test", mocker.MagicMock())
        assert len(results) == 1
