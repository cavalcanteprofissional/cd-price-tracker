import pytest
from scraper.filter import is_suspected_fanmade


def test_original_cd():
    assert is_suspected_fanmade("Thriller - Michael Jackson (CD Original)") is False


def test_fanmade_detected():
    assert is_suspected_fanmade("CD Fan Made - Artista Desconhecido") is True


def test_caseiro_detected():
    assert is_suspected_fanmade("CD caseiro de música brasileira") is True


def test_kit_personalizado():
    assert is_suspected_fanmade("Kit personalizado de CD") is True


def test_cd_virgem():
    assert is_suspected_fanmade("CD virgem para gravação") is True


def test_pirata():
    assert is_suspected_fanmade("CD pirata do Rock in Rio") is True


def test_bootleg():
    assert is_suspected_fanmade("Bootleg show 1994") is True


def test_reproducao():
    assert is_suspected_fanmade("Reprodução de CD raro") is True


def test_nao_original():
    assert is_suspected_fanmade("CD não original - cópia simples") is True


def test_descricao_ajuda():
    assert is_suspected_fanmade("CD Legítimo", description="produto artesanal") is True


def test_cd_original_loja():
    assert is_suspected_fanmade("CD Legítimo - Loja Oficial", description="produto lacrado original") is False
