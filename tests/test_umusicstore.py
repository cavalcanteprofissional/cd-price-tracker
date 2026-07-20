import pytest
from scraper.umusicstore import _try_api


class TestTryApi:
    def test_success_single_product(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            "productName": "CD Thriller Michael Jackson",
            "linkText": "thriller",
            "items": [{
                "sellers": [{"commertialOffer": {"Price": 49.90}}],
                "images": [{"imageUrl": "https://example.com/cover.jpg"}],
            }],
        }]
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("Thriller")
        assert len(items) == 1
        assert items[0]["title"] == "CD Thriller Michael Jackson"
        assert items[0]["price_text"] == "R$ 49.90"
        assert "thriller" in items[0]["listing_url"]

    def test_success_multiple_products(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"productName": "CD A", "linkText": "a", "items": [{"sellers": [{"commertialOffer": {"Price": 10}}], "images": []}]},
            {"productName": "CD B", "linkText": "b", "items": [{"sellers": [{"commertialOffer": {"Price": 20}}], "images": []}]},
        ]
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("test")
        assert len(items) == 2

    def test_empty_response(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("nonexistent")
        assert items == []

    def test_dict_response(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"productName": "CD Single", "linkText": "single", "items": [{"sellers": [{"commertialOffer": {"Price": 29.90}}], "images": []}]}
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("single")
        assert len(items) == 1

    def test_http_error(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 404
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("error")
        assert items == []

    def test_exception(self, mocker):
        mocker.patch("scraper.umusicstore.httpx.get", side_effect=Exception("timeout"))

        items = _try_api("error")
        assert items == []

    def test_duplicates_skipped(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"productName": "CD Thriller", "linkText": "thriller", "items": [{"sellers": [{"commertialOffer": {"Price": 49.90}}], "images": []}]},
            {"productName": "CD Thriller", "linkText": "thriller-2", "items": [{"sellers": [{"commertialOffer": {"Price": 39.90}}], "images": []}]},
        ]
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("thriller")
        assert len(items) == 1

    def test_no_sellers(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            "productName": "CD No Seller",
            "linkText": "no-seller",
            "items": [{"sellers": [], "images": []}],
        }]
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("test")
        assert items == []

    def test_zero_price_treated_as_no_price(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            "productName": "CD Free",
            "linkText": "free",
            "items": [{"sellers": [{"commertialOffer": {"Price": 0}}], "images": []}],
        }]
        mocker.patch("scraper.umusicstore.httpx.get", return_value=mock_resp)

        items = _try_api("free")
        assert len(items) == 1
        assert items[0]["price_text"] == ""
