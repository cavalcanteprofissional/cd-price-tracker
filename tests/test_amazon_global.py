import pytest
from scraper.utils import normalize
from scraper.amazon_global import MARKETPLACES


class TestMarketplaces:
    def test_has_three_marketplaces(self):
        assert set(MARKETPLACES.keys()) == {"amazon_us", "amazon_uk", "amazon_de"}

    def test_us_config(self):
        cfg = MARKETPLACES["amazon_us"]
        assert cfg["currency"] == "USD"
        assert "amazon.com" in cfg["search_url"]

    def test_uk_config(self):
        cfg = MARKETPLACES["amazon_uk"]
        assert cfg["currency"] == "GBP"
        assert "amazon.co.uk" in cfg["search_url"]

    def test_de_config(self):
        cfg = MARKETPLACES["amazon_de"]
        assert cfg["currency"] == "EUR"
        assert "amazon.de" in cfg["search_url"]


class TestScoringLogic:
    """Testa a logica de scoring sem mock (apenas manipulacao de dados)."""

    def test_album_token_penalty(self):
        """Candidato sem token do album deve receber penalidade."""
        from scraper.utils import token_similarity

        title = "The Dark Side of the Moon"
        artist = "Pink Floyd"
        expected_tokens = set(normalize(f"{title} {artist}").split())
        artist_tokens = set(normalize(artist).split())
        album_tokens = expected_tokens - artist_tokens
        assert album_tokens  # deve ter tokens exclusivos do album

        candidate_com_album = {"title": "The Dark Side of the Moon Pink Floyd CD"}
        candidate_sem_album = {"title": "Pink Floyd CD Collection"}

        def score(c):
            s = token_similarity(f"{title} {artist}", c["title"])
            title_norm = normalize(c["title"])
            has_album_token = any(t in title_norm for t in album_tokens)
            if not has_album_token:
                s *= 0.3
            return s

        score_com = score(candidate_com_album)
        score_sem = score(candidate_sem_album)
        assert score_com > score_sem, "candidato com token do album deve ter score maior"

    def test_artist_token_scoring(self):
        """Similaridade com artista deve influenciar o score."""
        from scraper.utils import token_similarity

        title = "Thriller"
        artist = "Michael Jackson"

        high_sim = token_similarity(f"{title} {artist}", "Thriller Michael Jackson CD Original")
        low_sim = token_similarity(f"{title} {artist}", "Smartphone Samsung")
        assert high_sim > low_sim
