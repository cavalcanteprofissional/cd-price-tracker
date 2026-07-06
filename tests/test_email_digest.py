import os
from string import Template


HTML_TPL = Template("""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Precos da Semana</h2>
  <p>Confira os precos dos CDs monitorados nesta semana.</p>
  <table style="width: 100%; border-collapse: collapse;">
    <tr style="background: #f3f4f6;">
      <th style="padding: 8px; text-align: left;">CD</th>
      <th style="padding: 8px; text-align: left;">Plataforma</th>
      <th style="padding: 8px; text-align: right;">Preco</th>
      <th style="padding: 8px; text-align: right;">Variacao</th>
    </tr>
    $rows
  </table>
  <p style="margin-top: 24px; font-size: 12px; color: #6b7280;">
    <a href="$unsubscribe_url">Cancelar inscricao</a>
  </p>
</body>
</html>
""")

ROW_TPL = Template("""
    <tr style="border-top: 1px solid #e5e7eb;">
      <td style="padding: 8px;">$title - $artist</td>
      <td style="padding: 8px;">$platform</td>
      <td style="padding: 8px; text-align: right;">R$$ $price</td>
      <td style="padding: 8px; text-align: right; color: $change_color;">$change</td>
    </tr>
""")


def render_digest(items: list[dict]) -> str:
    if not items:
        return "<html><body><p>Nenhum preco registrado esta semana.</p></body></html>"

    rows = ""
    for item in items:
        rows += ROW_TPL.substitute(
            title=item["title"],
            artist=item["artist"],
            platform=item["platform"],
            price=f"{item['price']:.2f}".replace(".", ","),
            change=item.get("change", "-"),
            change_color=item.get("change_color", "#6b7280"),
        )
    return HTML_TPL.substitute(rows=rows, unsubscribe_url="#")


def test_render_digest_empty():
    html = render_digest([])
    assert "<html" in html


def test_render_digest_with_data():
    items = [
        {
            "title": "Thriller",
            "artist": "Michael Jackson",
            "platform": "amazon",
            "price": 49.90,
            "change": "-R$ 5,00",
            "change_color": "green",
        }
    ]
    html = render_digest(items)
    assert "Thriller" in html
    assert "Michael Jackson" in html
    assert "amazon" in html


def test_render_digest_multiple():
    items = [
        {"title": "A", "artist": "Art A", "platform": "amazon", "price": 10.00, "change": "-", "change_color": "#6b7280"},
        {"title": "B", "artist": "Art B", "platform": "mercado_livre", "price": 20.00, "change": "+R$ 5,00", "change_color": "red"},
    ]
    html = render_digest(items)
    assert "A" in html
    assert "B" in html
    assert "mercado_livre" in html


def test_build_digest_items(mocker):
    mocker.patch("scraper.email_digest.supabase.table", autospec=True)
    from scraper.email_digest import build_digest_items
    result = build_digest_items()
    assert isinstance(result, list)
