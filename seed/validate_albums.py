#!/usr/bin/env python3
"""Valida e enriquece álbuns do seed via Last.fm API.

Uso:
    python -m seed.validate_albums

Requer LASTFM_API_KEY no ambiente ou scraper/.env.
Lê seed/products.json, gera seed/products_enriched.json.
"""

import json
import logging
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / "scraper" / ".env")

SEED_DIR = Path(__file__).resolve().parent
PRODUCTS_PATH = SEED_DIR / "products.json"
OUTPUT_PATH = SEED_DIR / "products_enriched.json"

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
MIN_CONFIDENCE = 0.6
REQUEST_DELAY = 0.25


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s]", "", text)


def token_similarity(a: str, b: str) -> float:
    a_tokens = set(_normalize(a).split())
    b_tokens = set(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    return len(intersection) / max(len(a_tokens), len(b_tokens))


def _pick_best_image(images: list[dict]) -> str | None:
    for size in ("mega", "extralarge", "large"):
        for img in images:
            if img.get("size") == size and img.get("#text"):
                return img["#text"]
    for img in images:
        if img.get("#text"):
            return img["#text"]
    return None


class LastFMClient:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._http = httpx.Client(timeout=15.0)

    def _get(self, params: dict) -> dict[str, Any]:
        params.setdefault("api_key", self._api_key)
        params.setdefault("format", "json")
        resp = self._http.get(LASTFM_API_URL, params=params)
        resp.raise_for_status()
        return resp.json()

    def search_album(self, title: str, artist: str) -> list[dict]:
        data = self._get(
            {"method": "album.search", "album": f"{artist} {title}", "limit": 10}
        )
        matches = data.get("results", {}).get("albummatches", {}).get("album", [])
        return matches

    def get_album_info(self, artist: str, album: str) -> dict | None:
        try:
            data = self._get(
                {"method": "album.getInfo", "artist": artist, "album": album}
            )
            return data.get("album")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def pick_best_match(
        self, items: list[dict], expected_title: str, expected_artist: str
    ) -> dict | None:
        best = None
        best_score = 0.0
        for item in items:
            result_title = item.get("name", "")
            result_artist = item.get("artist", "")
            title_score = token_similarity(expected_title, result_title)
            artist_score = token_similarity(expected_artist, result_artist)
            score = title_score * 0.6 + artist_score * 0.4
            if score > best_score:
                best_score = score
                best = item
        if best and best_score >= MIN_CONFIDENCE:
            return best
        return None


def validate_item(client: LastFMClient, item: dict) -> dict:
    title = item["title"]
    artist = item["artist"]

    result = dict(item)
    result["lastfm_url"] = None
    result["release_date"] = None
    result["genre"] = []
    result["lastfm_listeners"] = None

    try:
        results = client.search_album(title, artist)
        if not results:
            logger.warning("  NÃO ENCONTRADO — %s - %s", artist, title)
            return result

        match = client.pick_best_match(results, title, artist)
        if not match:
            logger.warning("  BAIXA CONFIANÇA — %s - %s", artist, title)
            for r in results:
                logger.warning("    candidato: %s — %s", r.get("name"), r.get("artist"))
            return result

        result["lastfm_url"] = match.get("url")
        result["lastfm_listeners"] = match.get("listeners")

        images = match.get("image", [])
        cover = _pick_best_image(images)
        if cover and not result.get("cover_url"):
            result["cover_url"] = cover

        info = client.get_album_info(match["artist"], match["name"])
        if info:
            if not result.get("cover_url"):
                cover2 = _pick_best_image(info.get("image", []))
                if cover2:
                    result["cover_url"] = cover2

            wiki = info.get("wiki", {})
            if wiki.get("published"):
                result["release_date"] = wiki["published"]

            tags = info.get("tags", {}).get("tag", [])
            result["genre"] = [t.get("name", "") for t in tags[:5]]

        logger.info(
            "  OK — %s — %s [%s] (%s ouvintes)",
            match.get("name"),
            result["release_date"] or "sem data",
            ", ".join(result["genre"]) if result["genre"] else "sem tags",
            result["lastfm_listeners"] or "?",
        )

    except httpx.HTTPStatusError as e:
        logger.error("  ERRO HTTP %s — %s - %s", e.response.status_code, artist, title)
    except Exception as e:
        logger.error("  ERRO — %s - %s: %s", artist, title, e)

    time.sleep(REQUEST_DELAY)
    return result


def main() -> None:
    if not LASTFM_API_KEY:
        logger.error(
            "Last.fm API Key não encontrada.\n\n"
            "Crie uma conta em https://www.last.fm/api/account/create e gere sua chave.\n"
            "Depois defina no arquivo scraper/.env:\n"
            "  LASTFM_API_KEY=sua_chave_aqui"
        )
        return

    if not PRODUCTS_PATH.exists():
        logger.error("Arquivo não encontrado: %s", PRODUCTS_PATH)
        return

    products = json.loads(PRODUCTS_PATH.read_text("utf-8"))
    logger.info("Carregados %d produtos de %s", len(products), PRODUCTS_PATH.name)

    client = LastFMClient(LASTFM_API_KEY)
    enriched = [validate_item(client, item) for item in products]

    found = sum(1 for p in enriched if p["lastfm_url"])
    missing = sum(1 for p in enriched if not p["lastfm_url"])

    logger.info("")
    logger.info("=== RESUMO ===")
    logger.info("Encontrados:   %d", found)
    logger.info("Não encontrados: %d", missing)
    logger.info("")

    OUTPUT_PATH.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), "utf-8")
    logger.info("Gerado: %s", OUTPUT_PATH)

    if missing:
        logger.info("Produtos para revisão manual:")
        for p in enriched:
            if not p["lastfm_url"]:
                logger.info("  - %s — %s", p["artist"], p["title"])


if __name__ == "__main__":
    main()
