---
name: cd-price-tracker
description: Sistema completo de monitoramento semanal de preços de CDs (Compact Disc) em Amazon, Mercado Livre e Shopee, com histórico de preços, filtro anti-fanmade/caseiro, digest semanal por email (double opt-in) e frontend em Next.js. Use este skill sempre que for construir, estender ou depurar qualquer parte deste sistema: scraper, banco Supabase, GitHub Actions cron, envio de email via Resend, ou o frontend Next.js do projeto.
---

# CD Price Tracker

Sistema de web scraping para acompanhar preços de uma lista curada de CDs (Compact Disc) em plataformas digitais, com histórico, notificação semanal por email e dashboard web.

## Estrutura do monorepo

```
cd-price-tracker/
├── .github/
│   └── workflows/
│       └── weekly-scrape.yml
│
├── scraper/
│   ├── main.py                    # orquestrador: itera products_platform_config, delega scraping
│   ├── amazon.py                  # scraper Amazon (URL fixa + Playwright stealth)
│   ├── mercadolivre.py            # scraper Mercado Livre (busca textual)
│   ├── shopee.py                  # scraper Shopee (busca textual, API interna + fallback Playwright)
│   ├── filter.py                  # filtro anti-fanmade/caseiro (regex)
│   ├── price_parser.py            # normalização de preço BRL para numeric
│   ├── models.py                  # dataclasses para tipagem dos dados entre scrapers e banco
│   ├── supabase_client.py         # cliente Supabase com service_role (escrita)
│   ├── email_digest.py            # montagem + envio do digest semanal via Resend
│   ├── alert.py                   # notificação de falha do pipeline
│   ├── requirements.txt
│   ├── .env.example
│   └── .python-version
│
├── frontend/                      # Next.js (App Router)
│   ├── app/
│   │   ├── page.tsx               # listagem dos CDs com último preço
│   │   ├── produto/
│   │   │   └── [id]/
│   │   │       └── page.tsx       # histórico + gráfico recharts
│   │   ├── cadastro/
│   │   │   └── page.tsx           # formulário de email
│   │   └── api/
│   │       ├── subscribe/
│   │       │   └── route.ts       # POST → cria subscriber + envia confirmação
│   │       ├── confirm/
│   │       │   └── route.ts       # GET → confirma token
│   │       └── unsubscribe/
│   │           └── route.ts       # GET → cancela inscrição
│   ├── components/
│   │   ├── price-card.tsx
│   │   ├── price-chart.tsx
│   │   └── subscribe-form.tsx
│   ├── lib/
│   │   └── supabase.ts            # client Supabase anon key (Server Components)
│   ├── next.config.js
│   ├── package.json
│   └── .env.example
│
├── tests/
│   ├── test_filter.py             # pytest: validar is_suspected_fanmade
│   └── test_price_parser.py       # pytest: validar parse_br_price
│
├── seed/
│   └── products.json              # ~10 CDs de teste para seed manual
│
└── README.md
```

## Visão geral da arquitetura

```
[seed/products.json — lista fixa de ~50 CDs curados]
                    │
GitHub Actions (cron semanal, toda segunda 09:00 BRT, timeout 30min)
                    │
         Script Python (scraper/main.py)
   ┌────────────────┼────────────────┐
   │                │                │
 Amazon          Mercado Livre      Shopee
(URL fixa)      (busca por texto)  (busca por texto / API interna)
   │                │                │
   └────────────────┴────────────────┘
                    │
         filtro anti-fanmade (regex)
                    │
         price_parser (R$ 49,90 → 49.90)
                    │
              Supabase (Postgres)
        grava price_history, consulta subscribers
                    │
        ┌───────────┴────────────┐
        │                        │
  Resend API                Next.js (Vercel)
  digest semanal            ├─ /            últimos preços
  aos confirmados           ├─ /produto/[id] histórico + gráfico
  + alerta de falha         ├─ /cadastro     form + double opt-in
                            └─ /api/unsubscribe  cancelamento
```

## Stack (tudo gratuito)

| Camada | Tecnologia | Observação |
|---|---|---|
| Scraper | Python + Playwright + BeautifulSoup + playwright-stealth | Playwright para páginas com JS/anti-bot; stealth plugin para evadir detecção |
| Agendamento | GitHub Actions (`schedule: cron`) | roda 1x/semana, sem servidor dedicado, timeout 30min |
| Banco de dados | Supabase (Postgres) | free tier até 500MB |
| Email | Resend | free tier: 100 emails/dia |
| Frontend | Next.js (App Router) + recharts | deploy na Vercel, free tier |
| Testes | Pytest | unitários para filter + price_parser |

## Decisões de produto já fechadas (não reabrir sem confirmar com o usuário)

1. **Lista de CDs é fixa e curada manualmente** (não há busca livre pelo usuário no frontend). A curadoria acontece direto no banco (tabela `products` + `product_platform_config`).
2. **Ordem de prioridade de implementação:** Amazon → Mercado Livre → Shopee. Nem todo CD precisa ter linha em todas as 3 plataformas — só cadastre `product_platform_config` para as plataformas em que aquele CD realmente é vendido.
3. **Amazon usa URL fixa por CD** (curada manualmente, um produto = um link).
4. **Mercado Livre e Shopee usam busca por texto** (`search_query` por CD), porque o vendedor/preço mais barato muda semana a semana. O script deve rodar a busca, filtrar fanmade, e escolher o **menor preço entre os anúncios legítimos restantes**.
5. **Filtro anti-fanmade/caseiro é OBRIGATÓRIO antes de gravar qualquer preço no banco.** Itens suspeitos são **excluídos automaticamente** (não aparecem no banco, no frontend, nem no email) — apenas logados separadamente para auditoria.
6. **Nome do vendedor/loja é obrigatório para Mercado Livre e Shopee** (campo `seller_name`). Para Amazon fica `null` a menos que seja explicitamente vendido por terceiro.
7. **Cadastro de email exige double opt-in** (confirmação por link antes de considerar o email ativo para receber o digest).
8. Como a lista de CDs é fixa e todo mundo recebe o mesmo digest, **não existe tabela de assinatura por produto** nesta versão — todo `subscriber` confirmado recebe o resumo semanal completo. (Deixe o schema fácil de estender para isso no futuro, mas não implemente agora.)
9. **Unsubscribe é tratado via token próprio** (não apenas respondendo email). Cada subscriber recebe um `unsubscribe_token` gerado no cadastro.

## Projeto Supabase

### Schema do banco (Postgres)

```sql
create table products (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  artist text not null,
  cover_url text,
  created_at timestamptz default now()
);

create table product_platform_config (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id) on delete cascade,
  platform text not null check (platform in ('amazon', 'mercado_livre', 'shopee')),
  amazon_url text,        -- obrigatório somente se platform = 'amazon'
  search_query text,      -- obrigatório somente se platform in ('mercado_livre','shopee')
  active boolean default true,
  created_at timestamptz default now()
);

create table price_history (
  id uuid primary key default gen_random_uuid(),
  product_platform_config_id uuid references product_platform_config(id) on delete cascade,
  price numeric(10,2) not null,
  currency text default 'BRL',
  availability text,           -- ex: 'in_stock', 'out_of_stock', 'unknown'
  seller_name text,             -- null para amazon direta
  listing_url text not null,    -- pode variar semana a semana em ML/Shopee
  scraped_at timestamptz default now()
);

create table scrape_log (
  id uuid primary key default gen_random_uuid(),
  product_platform_config_id uuid references product_platform_config(id) on delete set null,
  status text not null check (status in ('success', 'skipped_fanmade', 'error', 'not_found')),
  raw_title text,
  detail text,
  scraped_at timestamptz default now()
);

create table subscribers (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  confirmed boolean default false,
  confirmation_token text not null,
  unsubscribe_token text not null,
  created_at timestamptz default now()
);
```

### Índices

```sql
create index idx_price_history_config_scraped on price_history(product_platform_config_id, scraped_at desc);
create index idx_subscribers_confirmed on subscribers(confirmed);
create index idx_scrape_log_status on scrape_log(status);
create index idx_subscribers_unsubscribe on subscribers(unsubscribe_token);
```

### Row Level Security (RLS)

```sql
-- Tabelas públicas de leitura (anon key pode SELECT)
alter table products enable row level security;
alter table product_platform_config enable row level security;
alter table price_history enable row level security;

create policy "Leitura pública de products"
  on products for select using (true);

create policy "Leitura pública de product_platform_config"
  on product_platform_config for select using (true);

create policy "Leitura pública de price_history"
  on price_history for select using (true);

-- subscribers: inserção anônima + leitura só do próprio registro via token
alter table subscribers enable row level security;

create policy "Inserção anônima em subscribers"
  on subscribers for insert with check (true);

create policy "Leitura própria via confirmation_token"
  on subscribers for select using (confirmation_token = current_setting('request.jwt.claims', true)::json->>'token');

create policy "Leitura própria via unsubscribe_token"
  on subscribers for select using (unsubscribe_token = current_setting('request.jwt.claims', true)::json->>'token');

create policy "Atualização própria via unsubscribe_token"
  on subscribers for update using (unsubscribe_token = current_setting('request.jwt.claims', true)::json->>'token');

-- scrape_log: sem acesso público (só service_role)
alter table scrape_log enable row level security;

create policy "Acesso service_role ao scrape_log"
  on scrape_log for all using (false);
```

## Filtro anti-fanmade / caseiro

Aplicar **antes** de gravar qualquer resultado em `price_history`. Se der match, gravar em `scrape_log` com status `skipped_fanmade` e **não** gravar em `price_history`.

```python
import re
import unicodedata

def normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text

FANMADE_PATTERNS = [
    r'\bfan\s*made\b',
    r'\bfanmade\b',
    r'\bcaseir[oa]\b',
    r'\bartesanal\b',
    r'\bimpressao\s+domestica\b',
    r'\bnao\s+original\b',
    r'\bkit\s+personalizad[oa]\b',
    r'\breproducao\b',
    r'\bpersonalizad[oa]\b.{0,15}\bcd\b',
    r'\bcd\b.{0,15}\bpersonalizad[oa]\b',
    r'\bcd\s+virgem\b',
    r'\bpirata\b',
    r'\bbootleg\b',
]

_compiled = [re.compile(p) for p in FANMADE_PATTERNS]

def is_suspected_fanmade(title: str, description: str = "") -> bool:
    text = normalize(f"{title} {description}")
    return any(p.search(text) for p in _compiled)
```

> Nota para quem for iterar nisso: este filtro é probabilístico. Sempre que ajustar os padrões, rode contra o `scrape_log` histórico para checar falsos positivos/negativos antes de subir pra produção.

## Price parser (normalização de preço BRL)

```python
import re

def parse_br_price(text: str) -> float:
    """Converte strings como 'R$ 49,90' ou '1.234,56' para float."""
    text = text.strip()
    text = re.sub(r'[R$\s]', '', text)
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    return float(text)
```

## Models (dataclasses)

`scraper/models.py`:

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ScrapedProduct:
    title: str
    price: Decimal
    currency: str
    availability: str        # 'in_stock' | 'out_of_stock' | 'unknown'
    seller_name: str | None
    listing_url: str
    platform: str            # 'amazon' | 'mercado_livre' | 'shopee'

@dataclass
class ScrapeResult:
    config_id: str
    product_id: str
    status: str              # 'success' | 'skipped_fanmade' | 'error' | 'not_found'
    product: ScrapedProduct | None
    raw_title: str | None
    detail: str | None
```

## Lógica do scraper por plataforma

### Amazon (URL fixa)

**Estratégia:** Playwright headless + `playwright-stealth` para evadir detecção. Delay randômico 3–7s antes de cada requisição. User-agent realista de navegador Chrome Windows.

**Seletores CSS:**
- Título: `#productTitle`
- Preço inteiro: `.a-price-whole`
- Preço centavos: `.a-price-fraction`
- Disponibilidade: `#availability span`

**Nota sobre múltiplos sellers na Amazon:** Uma mesma página pode mostrar preço de diferentes vendedores no box "Outros vendedores". O seletor `.a-price-whole` captura apenas o preço principal (Amazon direta ou primeiro seller). Para esta versão, considerar apenas o preço principal — se houver necessidade de capturar o menor entre múltiplos sellers, será uma melhoria futura.

**Fluxo:**
```
1. playwright_stealth.stealth_sync(context) antes de navegar
2. Acessa amazon_url com timeout 30s, wait_until domcontentloaded
3. Delay randômico 2-5s após carregar
4. Extrai título (textContent de #productTitle)
5. Extrai preço: .a-price-whole + .a-price-fraction → concatena → parse_br_price
6. is_suspected_fanmade(título)?
   - Sim → grava scrape_log(status='skipped_fanmade') e para
   - Não → grava price_history(seller_name=null, listing_url=amazon_url)
7. Em caso de timeout/CAPTCHA/bloqueio → retry até 3x com backoff, depois loga error
```

### Mercado Livre (busca por texto)

**Estratégia:** Playwright headless (sem stealth, ML é menos agressivo). URL de busca: `https://lista.mercadolivre.com.br/{search_query}`

**Seletores CSS:**
- Card do resultado: `ol.ui-search-layout > li.ui-search-layout__item`
- Título: `.ui-search-item__title`
- Preço: `.andes-money-amount__fraction`
- Vendedor: `.ui-search-item__seller-info`
- Link: `a.ui-search-link` → atributo `href`

**Fluxo:**
```
1. Monta URL: f"https://lista.mercadolivre.com.br/{quote(search_query)}"
2. Acessa via Playwright, wait_until domcontentloaded
3. Coleta até 20 primeiros resultados (li.ui-search-layout__item)
4. Para cada resultado extrai {titulo, preco, vendedor, url}
5. Remove da lista qualquer item onde is_suspected_fanmade(titulo) == True
   (cada removido gera scrape_log(status='skipped_fanmade'))
6. Se lista vazia → scrape_log(status='not_found') e para
7. Escolhe o item de menor preço (parse_br_price) entre os restantes
8. Grava price_history(price, seller_name=vendedor, listing_url=url)
```

### Shopee (busca por texto)

**Estratégia primária:** API interna `https://shopee.com.br/api/v4/search/search_items` via `httpx`. Mais confiável e leve que renderizar a página inteira.

**Parâmetros da API:**
```
GET /api/v4/search/search_items?by=relevancy&keyword={search_query}&limit=20&newest=0&order=desc&page_type=search

Headers:
  - User-Agent: realista (Chrome Windows)
  - x-request-source: desktop
  - Referer: https://shopee.com.br/
  - Cookie: SPSC=...  (obtido de uma sessão anônima via Playwright)

Response (items[]):
  - item_basic.name              → título
  - item_basic.price             → inteiro, dividir por 100000
  - item_basic.shop_location     → vendedor (fallback: shopid)
  - item_basic.itemid            → montar URL: https://shopee.com.br/product/{shopid}/{itemid}
```

**Nota sobre bloqueio da API:** Se a API retornar 403 ou response vazio, fazer fallback para Playwright:
1. Abrir `https://shopee.com.br/search?keyword={search_query}`
2. Aguardar o seletor `div.shopee-search-item-result__item` renderizar
3. Extrair dados do DOM ou interceptar a resposta XHR da API (page.route)

**Fluxo:**
```
1. Tenta API primária com httpx + headers (timeout 15s)
2. Se 403/429/erro → fallback para Playwright
3. Extrai de cada resultado: {titulo, preco/100000, vendedor, url}
4. Filtra fanmade (igual ML)
5. Escolhe menor preço → grava price_history
```

### Regras gerais de scraping (todas as plataformas)

- **Retry:** 3 tentativas por scrape com `tenacity` (backoff exponencial: 2s, 4s, 8s) em caso de timeout/CAPTCHA/erro de rede.
- **Delay randômico:** 2–6s entre scraping de cada produto dentro da mesma plataforma.
- **User-agent realista** e headers de navegador normal via `playwright-stealth`.
- Rodar 1x/semana já reduz bastante o risco — **não** implementar scraping mais frequente sem repensar a estratégia de anti-bot.
- Se uma plataforma falhar (timeout, captcha, bloqueio), **não travar o pipeline inteiro**: logar erro em `scrape_log(status='error')` e seguir para o próximo produto/plataforma.
- **Logging estruturado:** usar módulo `logging` com formato `%(asctime)s [%(levelname)s] %(name)s: %(message)s`. Não usar `print`.
- Amazon é a plataforma mais sensível a bloqueio — implementar e validar essa primeiro, isoladamente, antes de integrar ML e Shopee.
- **Concorrência:** `main.py` executa os scrapers sequencialmente por produto/plataforma para evitar sobrecarga. Se no futuro o volume crescer, considerar `ThreadPoolExecutor` com max_workers=3 (um por plataforma).

## Orquestrador (main.py)

```python
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

def process_config(config: dict) -> ScrapeResult:
    platform = config["platform"]
    try:
        if platform == "amazon":
            result = scrape_amazon(config)
        elif platform == "mercado_livre":
            result = scrape_mercadolivre(config)
        elif platform == "shopee":
            result = scrape_shopee(config)
        else:
            raise ValueError(f"Plataforma desconhecida: {platform}")

        persist(result)
        return result
    except Exception as e:
        logger.error("Erro ao processar %s/%s: %s", config["product_id"], platform, e)
        persist(ScrapeResult(
            config_id=config["id"],
            product_id=config["product_id"],
            status="error",
            product=None,
            raw_title=None,
            detail=str(e),
        ))
        return None

def main():
    configs = supabase.table("product_platform_config") \
        .select("*, products!inner(*)") \
        .eq("active", True) \
        .execute()

    logger.info("Iniciando scrape de %d configs", len(configs.data))
    results = []
    for cfg in configs.data:
        result = process_config(cfg)
        results.append(result)

    logger.info("Scrape concluído. Success: %d | Errors: %d | Skipped/Fanmade: %d",
        sum(1 for r in results if r and r.status == "success"),
        sum(1 for r in results if r and r.status == "error"),
        sum(1 for r in results if r and r.status == "skipped_fanmade"))

    send_digest()
```

## Supabase Client (Python)

`scraper/supabase_client.py`:

```python
import os
from supabase import create_client, Client

_url = os.environ["SUPABASE_URL"]
_key = os.environ["SUPABASE_SERVICE_KEY"]

supabase: Client = create_client(_url, _key)
```

Usar `supabase.table("price_history").insert(...).execute()` para escrita. Consultas de subscribers e products via service_role key (sem RLS).

## Alerta de falha do pipeline

`scraper/alert.py`:

```python
import os
import resend

resend.api_key = os.environ["RESEND_API_KEY"]

def send_alert(message: str) -> None:
    resend.Emails.send({
        "from": os.environ["RESEND_FROM_EMAIL"],
        "to": os.environ["ALERT_EMAIL"],
        "subject": "[CD PRICE TRACKER] Falha no pipeline semanal",
        "text": message,
    })
```

O `scraper/main.py` deve envolver toda execução em try/except:

```python
import sys, traceback
from alert import send_alert

def main():
    try:
        # pipeline principal
    except Exception:
        error_msg = traceback.format_exc()
        send_alert(f"Pipeline semanal falhou:\n\n{error_msg}")
        sys.exit(1)
```

## GitHub Actions (agendamento)

```yaml
name: Weekly CD Price Scrape
on:
  schedule:
    - cron: '0 12 * * 1'  # toda segunda-feira, 12:00 UTC (~09:00 BRT)
  workflow_dispatch: {}     # permite rodar manualmente pra testar

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r scraper/requirements.txt
      - run: playwright install --with-deps chromium
      - run: python scraper/main.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          RESEND_FROM_EMAIL: ${{ secrets.RESEND_FROM_EMAIL }}
          ALERT_EMAIL: ${{ secrets.ALERT_EMAIL }}
```

`workflow_dispatch` é importante para permitir rodar manualmente durante o desenvolvimento, sem esperar o cron.

## Fluxo de email (Resend + double opt-in)

**Cadastro:**
1. Frontend (`/cadastro`) envia POST para API route `/api/subscribe` com o email.
2. API route gera `confirmation_token` (uuid) e `unsubscribe_token` (uuid), grava em `subscribers` com `confirmed=false`.
3. Resend envia email com assunto "Confirme seu email" e link: `https://SEU_DOMINIO/api/confirm?token=TOKEN`.

**Confirmação:**
1. API route `/api/confirm` recebe o token, busca subscriber correspondente.
2. Se válido → `confirmed=true`. Se inválido/expirado → mensagem de erro amigável com opção de reenviar.

**Unsubscribe:**
1. Todo email digest inclui link: `https://SEU_DOMINIO/api/unsubscribe?token=UNSUBSCRIBE_TOKEN`
2. API route `/api/unsubscribe` recebe o token, marca `confirmed=false` ou deleta o registro.
3. Página de confirmação amigável: "Você foi removido da lista."

**Digest semanal:**
1. `email_digest.py` busca `subscribers WHERE confirmed=true`.
2. Monta o resumo HTML (tabela com CD → plataforma → preço atual → variação vs. semana anterior).
3. Envia via Resend respeitando rate limit: **máximo 100 emails/dia** (free tier). Se houver mais que 100 subscribers confirmados, enviar em lote de 10 a cada 5s e parar ao atingir o limite.

## Template do email digest

`scraper/email_digest.py`:

```python
import os
import resend
from string import Template

resend.api_key = os.environ["RESEND_API_KEY"]

HTML_TPL = Template("""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Preços da Semana</h2>
  <p>Olá! Aqui estão os preços dos CDs monitorados nesta semana.</p>
  <table style="width: 100%; border-collapse: collapse;">
    <tr style="background: #f3f4f6;">
      <th style="padding: 8px; text-align: left;">CD</th>
      <th style="padding: 8px; text-align: left;">Plataforma</th>
      <th style="padding: 8px; text-align: right;">Preço</th>
      <th style="padding: 8px; text-align: right;">Variação</th>
    </tr>
    $rows
  </table>
  <p style="margin-top: 24px; font-size: 12px; color: #6b7280;">
    <a href="$unsubscribe_url">Cancelar inscrição</a>
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

def send_digest(subscriber_email: str, unsubscribe_token: str, items: list[dict]):
    rows = ""
    for item in items:
        change = item.get("change", "—")
        change_color = "green" if change != "—" and change < 0 else "red"
        rows += ROW_TPL.substitute(
            title=item["title"],
            artist=item["artist"],
            platform=item["platform"],
            price=item["price"],
            change=change,
            change_color=change_color,
        )

    html = HTML_TPL.substitute(
        rows=rows,
        unsubscribe_url=f"{os.environ['NEXT_PUBLIC_SITE_URL']}/api/unsubscribe?token={unsubscribe_token}"
    )

    resend.Emails.send({
        "from": os.environ["RESEND_FROM_EMAIL"],
        "to": subscriber_email,
        "subject": "Preços da Semana - CD Price Tracker",
        "html": html,
    })
```

## Frontend (Next.js)

### Páginas mínimas

- `/` — lista dos CDs monitorados com o preço mais recente por plataforma (cards ou tabela). Consulta via Server Component com `supabase.from("products").select("..., product_platform_config(...), price_history(...)")`.
- `/produto/[id]` — histórico de preços do CD com gráfico (recharts), separado por plataforma/vendedor.
- `/cadastro` — formulário simples de email → chama `/api/subscribe`.

### API Routes

- `/api/subscribe` (POST) — valida email, gera `confirmation_token` + `unsubscribe_token`, insere em `subscribers`, dispara email de confirmação via Resend.
- `/api/confirm` (GET) — recebe `?token=...`, marca `confirmed=true`.
- `/api/unsubscribe` (GET) — recebe `?token=...`, marca `confirmed=false`.

### Client Supabase (frontend)

`frontend/lib/supabase.ts`:

```typescript
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

Usar `@supabase/supabase-js` direto nas Server Components do Next.js para leitura (RLS público). Nunca expor a `service_role key` no frontend.

### next.config.js

```js
/** @type {import('next').NextConfig} */
module.exports = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**" },
    ],
  },
};
```

### Pacotes npm

```json
{
  "dependencies": {
    "next": "^14",
    "react": "^18",
    "react-dom": "^18",
    "@supabase/supabase-js": "^2",
    "recharts": "^2",
    "resend": "^3"
  }
}
```

## Variáveis de ambiente

### Scraper (`scraper/.env`)

```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
RESEND_API_KEY=
RESEND_FROM_EMAIL=
ALERT_EMAIL=                    # seu email para receber alertas de falha
```

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=            # backend-only (API routes)
RESEND_API_KEY=
RESEND_FROM_EMAIL=
NEXT_PUBLIC_SITE_URL=            # usado no link de confirmação e unsubscribe
```

## Scraper requirements.txt

```txt
playwright>=1.45
playwright-stealth>=1.0
beautifulsoup4>=4.12
supabase>=2.5
httpx>=0.27
tenacity>=8.3
pytest>=8.0
resend>=0.8
python-dotenv>=1.0
```

## Seed (products.json)

`seed/products.json` — estrutura para seed manual no Supabase:

```json
[
  {
    "title": "Thriller",
    "artist": "Michael Jackson",
    "cover_url": null,
    "platforms": [
      { "platform": "amazon", "amazon_url": "https://www.amazon.com.br/dp/B001234567" },
      { "platform": "mercado_livre", "search_query": "thriller michael jackson cd original" },
      { "platform": "shopee", "search_query": "thriller michael jackson cd" }
    ]
  },
  {
    "title": "Abbey Road",
    "artist": "The Beatles",
    "cover_url": null,
    "platforms": [
      { "platform": "amazon", "amazon_url": "https://www.amazon.com.br/dp/B000123456" },
      { "platform": "mercado_livre", "search_query": "abbey road beatles cd original" }
    ]
  },
  {
    "title": "The Dark Side of the Moon",
    "artist": "Pink Floyd",
    "cover_url": null,
    "platforms": [
      { "platform": "mercado_livre", "search_query": "dark side of the moon pink floyd cd" },
      { "platform": "shopee", "search_query": "dark side of the moon pink floyd cd" }
    ]
  }
]
```

> Inserir primeiro na tabela `products`, depois usar o `id` retornado para inserir em `product_platform_config`.

## Testes

### `tests/test_filter.py`

```python
import pytest
from scraper.filter import is_suspected_fanmade

def test_original_cd():
    assert is_suspected_fanmade("Thriller - Michael Jackson (CD Original)") == False

def test_fanmade_detected():
    assert is_suspected_fanmade("CD Fan Made - Artista Desconhecido") == True

def test_caseiro_detected():
    assert is_suspected_fanmade("CD caseiro de música brasileira") == True

def test_kit_personalizado():
    assert is_suspected_fanmade("Kit personalizado de CD") == True

def test_cd_virgem():
    assert is_suspected_fanmade("CD virgem para gravação") == True

def test_pirata():
    assert is_suspected_fanmade("CD pirata do Rock in Rio") == True

def test_bootleg():
    assert is_suspected_fanmade("Bootleg show 1994") == True

def test_reproducao():
    assert is_suspected_fanmade("Reprodução de CD raro") == True

def test_nao_original():
    assert is_suspected_fanmade("CD não original - cópia simples") == True

def test_descricao_ajuda():
    assert is_suspected_fanmade("CD Legítimo", description="produto artesanal") == True

def test_cd_original_loja():
    assert is_suspected_fanmade("CD Legítimo - Loja Oficial", description="produto lacrado original") == False
```

### `tests/test_price_parser.py`

```python
import pytest
from scraper.price_parser import parse_br_price

def test_simple():
    assert parse_br_price("R$ 49,90") == 49.90

def test_thousands():
    assert parse_br_price("R$ 1.234,56") == 1234.56

def test_no_symbol():
    assert parse_br_price("29,99") == 29.99

def test_whitespace():
    assert parse_br_price("  R$ 5,00  ") == 5.0

def test_integer():
    assert parse_br_price("R$ 100") == 100.0
```

Rodar com:

```bash
cd cd-price-tracker && pip install -r scraper/requirements.txt && pytest tests/ -v
```

## Edge cases a tratar

- Produto sem nenhum resultado válido na busca (tudo filtrado como fanmade, ou zero resultados) → `scrape_log(status='not_found')`, não quebra o restante do pipeline.
- Preço com formatação diferente por plataforma (ex: "R$ 49,90" vs "49.90") → normalizar para `numeric` antes de gravar via `parse_br_price`.
- Confirmação de email com token expirado ou já usado → mensagem clara, opção de reenviar confirmação.
- Falha de rede/timeout durante scraping de uma plataforma → retry 3x com backoff; se persistir, loga `error` e segue para o próximo.
- Preço zerado ou nulo raspado por engano (erro de parsing) → validar `price > 0` antes de gravar; se falhar, tratar como `error` no log, não gravar lixo no histórico.
- Limite de 100 emails/dia do Resend → se `count(subscribers.confirmed=true) > 100`, enviar apenas para os 100 primeiros e logar warning.
- Timezone: GitHub Actions roda em UTC. O cron `0 12 * * 1` = 09:00 BRT (segunda). Considerar horário de verão brasileiro (muda para 08:00 BRT). Aceitável para scraping semanal.
- Shopee API retornar 403/429 → fallback automático para Playwright (renderizar página completa).
- Amazon mostrar preço de seller diferente do principal → considerar apenas o preço do elemento `.a-price-whole` (preço principal). Se não houver, logar `error`.
- `cover_url` nulo no frontend → exibir placeholder genérico (ex: capa de CD cinza com símbolo de música).

## Ordem de implementação recomendada

1. **Setup do monorepo** — criar estrutura de diretórios, `requirements.txt`, `.env.example`, `.python-version`
2. **Supabase** — criar projeto, rodar schema SQL + RLS policies + seed manual de 5–10 CDs de teste
3. **filter.py + price_parser.py + models.py** — implementar + escrever testes unitários (pytest)
4. **Scraper Amazon** — implementar `amazon.py` com Playwright + stealth, validar local
5. **Scraper Mercado Livre** — implementar `mercadolivre.py`, validar busca + filtro
6. **Scraper Shopee** — implementar `shopee.py` via API interna + fallback Playwright
7. **supabase_client.py + main.py + alert.py** — unificar os 3 scrapers no orquestrador + logging + retry + alerta de falha
8. **GitHub Actions** — configurar workflow com secrets e timeout, testar via `workflow_dispatch`
9. **email_digest.py** — template HTML + integração com Resend + rate limiting + unsubscribe
10. **Frontend Next.js** — pages `/` e `/produto/[id]` (leitura), depois `/cadastro` + API routes (subscribe, confirm, unsubscribe)
11. **Deploy Vercel** — configurar domínio, env vars, testar fluxo completo
12. **Expandir lista** — após tudo validado, popular ~50 CDs definitivos via seed script
