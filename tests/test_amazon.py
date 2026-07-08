import pytest
from scraper.utils import normalize, token_similarity
from scraper.amazon import scrape_amazon, search_amazon


class TestNormalize:
    def test_lowercase(self):
        assert normalize("Thriller") == "thriller"

    def test_remove_accents(self):
        assert normalize("João") == "joao"

    def test_alphanumeric_only(self):
        assert normalize("CD Original! @ #").strip() == "cd original"

    def test_empty(self):
        assert normalize("") == ""

    def test_spaces(self):
        assert normalize("  espaços  ") == "espacos"


class TestTokenSimilarity:
    def test_identical(self):
        assert token_similarity("Thriller Michael Jackson", "Thriller Michael Jackson") == 1.0

    def test_partial(self):
        sim = token_similarity("Thriller Michael Jackson", "Thriller Jackson")
        assert sim == pytest.approx(0.666, rel=0.01)

    def test_no_overlap(self):
        assert token_similarity("Thriller", "Abbey Road") == 0.0

    def test_empty_a(self):
        assert token_similarity("", "Thriller") == 0.0

    def test_empty_both(self):
        assert token_similarity("", "") == 0.0

    def test_case_and_accent(self):
        assert token_similarity("João Silva", "joao silva") == 1.0


class TestScrapeAmazon:
    def test_success(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.query_selector.side_effect = lambda sel: {
            "#productTitle": mocker.MagicMock(text_content=lambda: "Thriller - Michael Jackson"),
            ".a-price-whole": mocker.MagicMock(text_content=lambda: "49"),
            ".a-price-fraction": mocker.MagicMock(text_content=lambda: "90"),
            "#availability span": mocker.MagicMock(text_content=lambda: "Em estoque"),
        }.get(sel)
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = scrape_amazon("https://amazon.com.br/dp/test", mock_context)
        assert result is not None
        assert result["title"] == "Thriller - Michael Jackson"
        assert result["price_text"] == "49,90"
        assert result["availability"] == "in_stock"

    def test_no_title(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.query_selector.return_value = None
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = scrape_amazon("https://amazon.com.br/dp/test", mock_context)
        assert result is None

    def test_no_price(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.query_selector.side_effect = lambda sel: {
            "#productTitle": mocker.MagicMock(text_content=lambda: "Thriller"),
        }.get(sel)
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = scrape_amazon("https://amazon.com.br/dp/test", mock_context)
        assert result is None

    def test_out_of_stock(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.query_selector.side_effect = lambda sel: {
            "#productTitle": mocker.MagicMock(text_content=lambda: "Thriller"),
            ".a-price-whole": mocker.MagicMock(text_content=lambda: "49"),
            ".a-price-fraction": mocker.MagicMock(text_content=lambda: "90"),
            "#availability span": mocker.MagicMock(text_content=lambda: "Indisponível"),
        }.get(sel)
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = scrape_amazon("https://amazon.com.br/dp/test", mock_context)
        assert result["availability"] == "out_of_stock"

    def test_exception_handled(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.goto.side_effect = Exception("Timeout")
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = scrape_amazon("https://amazon.com.br/dp/test", mock_context)
        assert result is None


class TestSearchAmazon:
    def test_finds_match(self, mocker):
        mock_page = mocker.MagicMock()
        mock_div = mocker.MagicMock()

        mock_link = mocker.MagicMock()
        mock_link.text_content.return_value = "Thriller - Michael Jackson (CD Original)"
        mock_link.get_attribute.return_value = "/dp/B001"

        mock_price = mocker.MagicMock()
        mock_price.text_content.return_value = "R$ 49,90"

        mock_div.query_selector.side_effect = lambda sel: {
            "h2 a": mock_link,
            ".a-price .a-offscreen": mock_price,
        }.get(sel)

        mock_page.query_selector_all.return_value = [mock_div]
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = search_amazon("Thriller", "Michael Jackson", mock_context)
        assert result is not None
        assert "Thriller" in result["title"]

    def test_no_results(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.query_selector_all.return_value = []
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = search_amazon("Nonexistent Album XYZ", "Unknown", mock_context)
        assert result is None

    def test_low_confidence_skipped(self, mocker):
        mock_page = mocker.MagicMock()
        mock_div = mocker.MagicMock()

        mock_link = mocker.MagicMock()
        mock_link.text_content.return_value = "Smartphone Galaxy S24"
        mock_link.get_attribute.return_value = "/dp/B002"

        mock_price = mocker.MagicMock()
        mock_price.text_content.return_value = "R$ 4999,00"

        mock_div.query_selector.side_effect = lambda sel: {
            "h2 a": mock_link,
            ".a-price .a-offscreen": mock_price,
        }.get(sel)

        mock_page.query_selector_all.return_value = [mock_div]
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = search_amazon("Thriller", "Michael Jackson", mock_context)
        assert result is None

    def test_fallback_when_no_price_in_search(self, mocker):
        mock_page = mocker.MagicMock()

        mock_link = mocker.MagicMock()
        mock_link.text_content.return_value = "CD Thriller Michael Jackson Original"
        mock_link.get_attribute.return_value = "/dp/B003"

        mock_div = mocker.MagicMock()
        mock_div.query_selector.side_effect = lambda sel: {
            "h2 a": mock_link,
        }.get(sel)

        def search_side_effect(sel):
            if sel == "div[data-component-type='s-search-result']":
                return [mock_div]
            if sel == ".a-price-whole":
                return mocker.MagicMock(text_content=lambda: "59")
            if sel == ".a-price-fraction":
                return mocker.MagicMock(text_content=lambda: "90")
            return None

        mock_page.query_selector_all.return_value = [mock_div]
        mock_page.query_selector.side_effect = search_side_effect
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = search_amazon("Thriller", "Michael Jackson", mock_context)
        assert result is not None
        assert result["price_text"] == "59,90"

    def test_exception_handled(self, mocker):
        mock_page = mocker.MagicMock()
        mock_page.goto.side_effect = Exception("Timeout")
        mock_context = mocker.MagicMock()
        mock_context.new_page.return_value = mock_page

        result = search_amazon("Thriller", "Michael Jackson", mock_context)
        assert result is None
