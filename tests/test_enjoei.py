import pytest
from scraper.enjoei import _extract_from_api, _extract_title_from_href


class TestExtractFromApi:
    def test_graphql_search_products(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "searchProductsForStore": {
                        "edges": [
                            {"node": {"title": "CD Thriller Michael Jackson", "price": 49.90, "slug": "cd-thriller"}},
                            {"node": {"title": "CD Abbey Road Beatles", "price": 39.90, "slug": "cd-abbey-road"}},
                        ]
                    }
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert len(items) == 2
        assert items[0]["title"] == "CD Thriller Michael Jackson"
        assert "49,90" in items[0]["price_text"]
        assert items[0]["listing_url"] == "cd-thriller"

    def test_graphql_search_products_alternative(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "searchProducts": {
                        "edges": [
                            {"node": {"title": "CD Test", "price": 25.00, "slug": "cd-test"}},
                        ]
                    }
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert len(items) == 1

    def test_graphql_products_field(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "products": [
                        {"title": "CD Direct", "price": 15.00, "slug": "cd-direct"},
                    ]
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert len(items) == 1

    def test_empty_api_results(self):
        items = _extract_from_api([])
        assert items == []

    def test_no_matching_url(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/some-other-api",
            "data": {"data": {"products": [{"title": "CD X"}]}}
        }]
        items = _extract_from_api(api_results)
        assert items == []

    def test_skip_missing_title(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "searchProductsForStore": {
                        "edges": [
                            {"node": {"price": 10.00, "slug": "no-title"}},
                        ]
                    }
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert items == []

    def test_skip_missing_price(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "searchProductsForStore": {
                        "edges": [
                            {"node": {"title": "No Price", "slug": "no-price"}},
                        ]
                    }
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert items == []

    def test_seller_from_dict(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "searchProductsForStore": {
                        "edges": [
                            {"node": {"title": "CD Com Vendedor", "price": 50.00, "slug": "cd-vendedor", "seller": {"name": "Loja X"}}},
                        ]
                    }
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert len(items) == 1
        assert items[0]["seller_name"] == "Loja X"

    def test_url_from_url_field(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "searchProductsForStore": {
                        "edges": [
                            {"node": {"title": "CD URL Field", "price": 30.00, "url": "https://enjoei.com.br/p/custom-url"}},
                        ]
                    }
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert items[0]["listing_url"] == "https://enjoei.com.br/p/custom-url"

    def test_no_listing_url_fallback_empty(self):
        api_results = [{
            "url": "https://www.enjoei.com.br/graphql-search-x",
            "data": {
                "data": {
                    "searchProductsForStore": {
                        "edges": [
                            {"node": {"title": "CD No URL No Slug", "price": 20.00}},
                        ]
                    }
                }
            }
        }]
        items = _extract_from_api(api_results)
        assert len(items) == 1
        assert items[0]["listing_url"] == ""


class TestExtractTitleFromHref:
    def test_p_slug(self):
        assert _extract_title_from_href("/p/thriller-michael-jackson-123") == "Thriller Michael Jackson"

    def test_produto_slug(self):
        assert _extract_title_from_href("/produto/cd-abbey-road-456") == "Cd Abbey Road"

    def test_item_slug(self):
        assert _extract_title_from_href("/item/cd-dark-side-789") == "Cd Dark Side"

    def test_empty_href(self):
        assert _extract_title_from_href("") == ""

    def test_no_match(self):
        assert _extract_title_from_href("/about") == ""

    def test_none(self):
        assert _extract_title_from_href(None) == ""
