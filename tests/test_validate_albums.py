import httpx
import pytest
from seed.validate_albums import token_similarity, _normalize, _pick_best_image, LastFMClient


class TestNormalize:
    def test_lowercase(self):
        assert _normalize("Thriller") == "thriller"

    def test_remove_accents(self):
        assert _normalize("João") == "joao"

    def test_alphanumeric_only(self):
        assert _normalize("CD Original! @ #").strip() == "cd original"


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


class TestPickBestImage:
    def test_prefers_mega(self):
        images = [
            {"size": "small", "#text": "small.jpg"},
            {"size": "mega", "#text": "mega.jpg"},
            {"size": "large", "#text": "large.jpg"},
        ]
        assert _pick_best_image(images) == "mega.jpg"

    def test_falls_back_to_any(self):
        images = [
            {"size": "small", "#text": "small.jpg"},
        ]
        assert _pick_best_image(images) == "small.jpg"

    def test_empty(self):
        assert _pick_best_image([]) is None


class TestLastFMClient:
    def test_search_album(self, mocker):
        client = LastFMClient("test-key")
        mock_json = {
            "results": {
                "albummatches": {
                    "album": [
                        {"name": "Thriller", "artist": "Michael Jackson",
                         "url": "https://last.fm/Thriller",
                         "image": [{"size": "large", "#text": "cover.jpg"}]}
                    ]
                }
            }
        }
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = mock_json
        mocker.patch.object(client._http, "get", return_value=mock_resp)

        results = client.search_album("Thriller", "Michael Jackson")
        assert len(results) == 1
        assert results[0]["name"] == "Thriller"

    def test_search_album_empty(self, mocker):
        client = LastFMClient("test-key")
        mock_resp = mocker.MagicMock()
        mock_resp.json.return_value = {"results": {"albummatches": {"album": []}}}
        mocker.patch.object(client._http, "get", return_value=mock_resp)

        results = client.search_album("Nonexistent", "Unknown")
        assert results == []

    def test_get_album_info_not_found(self, mocker):
        client = LastFMClient("test-key")
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 404

        class Mock404Error(Exception):
            response = mock_resp

        mock_404 = httpx.HTTPStatusError("not found", request=mocker.MagicMock(), response=mock_resp)
        mocker.patch.object(client._http, "get", side_effect=mock_404)

        result = client.get_album_info("Unknown", "Nonexistent")
        assert result is None

    def test_pick_best_match(self, mocker):
        client = LastFMClient("test-key")
        items = [
            {"name": "Thriller", "artist": "Michael Jackson"},
            {"name": "Beat It", "artist": "Michael Jackson"},
        ]
        best = client.pick_best_match(items, "Thriller", "Michael Jackson")
        assert best is not None
        assert best["name"] == "Thriller"

    def test_pick_best_match_low_confidence(self, mocker):
        client = LastFMClient("test-key")
        items = [
            {"name": "Completely Different", "artist": "Unknown Band"},
        ]
        best = client.pick_best_match(items, "Thriller", "Michael Jackson")
        assert best is None
