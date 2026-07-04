import logging
import os
from string import Template

import resend

from scraper.supabase_client import supabase

logger = logging.getLogger(__name__)

resend.api_key = os.environ["RESEND_API_KEY"]


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
      <td style="padding: 8px; text-align: right;">R$ $price</td>
      <td style="padding: 8px; text-align: right; color: $change_color;">$change</td>
    </tr>
""")


def build_digest_items() -> list[dict]:
    products = supabase.table("products") \
        .select("id, title, artist, product_platform_config(id, platform, price_history(price, scraped_at))") \
        .execute()

    items = []
    for product in products.data:
        for config in product.get("product_platform_config", []):
            prices = config.get("price_history", [])
            if not prices:
                continue
            latest = max(prices, key=lambda p: p["scraped_at"])
            prev = None
            if len(prices) > 1:
                sorted_prices = sorted(prices, key=lambda p: p["scraped_at"], reverse=True)
                prev = sorted_prices[1]["price"]

            change = None
            if prev:
                change = round(latest["price"] - prev, 2)

            items.append({
                "title": product["title"],
                "artist": product["artist"],
                "platform": config["platform"],
                "price": latest["price"],
                "change": f"R$ {change:+.2f}" if change is not None else "-",
                "change_color": ("green" if change and change < 0 else "red") if change else "#6b7280",
            })

    return items


def send_digest_emails():
    site_url = os.environ.get("NEXT_PUBLIC_SITE_URL", "https://cd-price-tracker.vercel.app")

    subscribers = supabase.table("subscribers") \
        .select("email, unsubscribe_token") \
        .eq("confirmed", True) \
        .limit(100) \
        .execute()

    if not subscribers.data:
        logger.info("Nenhum subscriber confirmado para enviar digest")
        return

    items = build_digest_items()
    if not items:
        logger.info("Nenhum item de preco para o digest")
        return

    logger.info("Enviando digest para %d subscribers com %d itens", len(subscribers.data), len(items))

    for idx, sub in enumerate(subscribers.data):
        rows = ""
        for item in items:
            rows += ROW_TPL.substitute(
                title=item["title"],
                artist=item["artist"],
                platform=item["platform"],
                price=item["price"],
                change=item["change"],
                change_color=item["change_color"],
            )

        html = HTML_TPL.substitute(
            rows=rows,
            unsubscribe_url=f"{site_url}/api/unsubscribe?token={sub['unsubscribe_token']}",
        )

        try:
            resend.Emails.send({
                "from": os.environ["RESEND_FROM_EMAIL"],
                "to": sub["email"],
                "subject": "Precos da Semana - CD Price Tracker",
                "html": html,
            })
            logger.debug("Digest enviado para %s", sub["email"])
        except Exception as e:
            logger.error("Falha ao enviar digest para %s: %s", sub["email"], e)

        if idx >= 99:
            logger.warning("Limite de 100 emails/dia do Resend atingido")
            break
