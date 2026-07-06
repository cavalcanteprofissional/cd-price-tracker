import pytest
from scraper.filter import is_suspected_fanmade


@pytest.mark.parametrize("title,description,expected", [
    ("Thriller - Michael Jackson (CD Original)", None, False),
    ("CD Legítimo - Loja Oficial", "produto lacrado original", False),
    ("Nevermind", None, False),
    ("", None, False),
    ("CD Fan Made - Artista Desconhecido", None, True),
    ("CD caseiro de música brasileira", None, True),
    ("Kit personalizado de CD", None, True),
    ("CD virgem para gravação", None, True),
    ("CD pirata do Rock in Rio", None, True),
    ("Bootleg show 1994", None, True),
    ("Reprodução de CD raro", None, True),
    ("CD não original - cópia simples", None, True),
    ("CD Legítimo", "produto artesanal", True),
    ("CD Original", "réplica artesanal", True),
    ("IMPRESSAO DOMESTICA", None, True),
    ("Cd Personalizado", None, True),
])
def test_is_suspected_fanmade(title, description, expected):
    assert is_suspected_fanmade(title, description) is expected
