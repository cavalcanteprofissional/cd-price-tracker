import pytest
from scraper.utils import normalize, token_similarity, first_selector, best_match


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
        assert token_similarity("A B C", "A B C") == 1.0

    def test_partial(self):
        sim = token_similarity("A B C", "A B")
        assert sim == pytest.approx(0.666, rel=0.01)

    def test_no_overlap(self):
        assert token_similarity("A", "B") == 0.0

    def test_empty_a(self):
        assert token_similarity("", "A") == 0.0

    def test_empty_both(self):
        assert token_similarity("", "") == 0.0


class TestFirstSelector:
    def test_finds_first_match(self):
        mock_parent = type("Mock", (), {})()
        el_a = object()
        el_b = object()
        calls = []

        def query_selector(sel):
            calls.append(sel)
            return el_a if sel == ".target" else None

        mock_parent.query_selector = query_selector
        result = first_selector(mock_parent, [".not-found", ".target", ".also-target"])
        assert result is el_a
        assert calls == [".not-found", ".target"]

    def test_returns_none_when_no_match(self):
        mock_parent = type("Mock", (), {})()
        mock_parent.query_selector = lambda sel: None
        result = first_selector(mock_parent, [".a", ".b"])
        assert result is None

    def test_empty_selectors(self):
        mock_parent = type("Mock", (), {})()
        mock_parent.query_selector = lambda sel: object()
        result = first_selector(mock_parent, [])
        assert result is None


class TestBestMatch:
    def test_returns_best(self):
        candidates = [
            {"title": "Album One Artist"},
            {"title": "Different Thing"},
            {"title": "Album One Artist Deluxe"},
        ]
        result = best_match(candidates, "Album One Artist", "Artist")
        assert result is candidates[0]

    def test_low_confidence_returns_none(self):
        candidates = [
            {"title": "Unrelated Product"},
        ]
        result = best_match(candidates, "Album One Artist", "Artist")
        assert result is None

    def test_empty_candidates(self):
        result = best_match([], "Album", "Artist")
        assert result is None
