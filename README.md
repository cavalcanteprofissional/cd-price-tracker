# CD Price Tracker

Acompanhe os preços de CDs (Compact Disc) em Amazon, Mercado Livre e Shopee — com scraping automático, histórico de preços, alertas por email e painel web.

## Como funciona

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│ Seed de CDs │───→│ Validar no   │───→│ Scrapers     │───→│ Histórico   │
│ (Last.fm)   │    │ Supabase     │    │ (Playwright) │    │ (Supabase)  │
└─────────────┘    └──────────────┘    └──────────────┘    └──────┬──────┘
                                                                  │
                    ┌──────────────────────────────────────────────┤
                    │                                              │
                    ▼                                              ▼
            ┌──────────────┐                              ┌──────────────┐
            │ Painel Web   │                              │ Email Digest │
            │ (Next.js)    │                              │ (Resend)     │
            └──────────────┘                              └──────────────┘
```

1. Uma lista curada de CDs fica no Supabase (com capa, artista, ano, gênero do Last.fm)
2. Sempre que um CD não tem URL ou termo de busca, o scraper descobre automaticamente
3. Toda segunda-feira às 09:00 BRT, o pipeline roda e coleta os preços
4. Um filtro inteligente remove anúncios de CDs caseiros, fanmade ou bootleg
5. Os preços são salvos e você vê o histórico em gráficos no painel
6. Assinantes recebem um digest semanal por email

## Painel Admin

| Página | Função |
|---|---|
| `/gerenciar` | Lista todos os CDs cadastrados com opção de remover |
| `/gerenciar/adicionar` | Busca álbum no Last.fm, seleciona plataformas, salva |

### Busca inteligente

```
🔍 Buscar álbum ou artista...

Filtrar por artista: [Michael Jackson] [Pink Floyd] [The Beatles]

6 resultados:
┌────────────────────────────────────┐
│ 💿  Thriller                       │
│     Michael Jackson                │
├────────────────────────────────────┤
│ 💿  The Dark Side of the Moon      │
│     Pink Floyd                     │
└────────────────────────────────────┘
```

Digite qualquer coisa — nome do álbum, artista, ou ambos. Os resultados aparecem com capa e artista. Clicando nos chips de artista, você filtra na hora (sem nova busca).

## Stack

| Camada | Tecnologia |
|---|---|
| Scraper | Python + Playwright + playwright-stealth |
| Agendamento | GitHub Actions (cron semanal) |
| Banco | Supabase (Postgres, free tier) |
| Email | Resend (free tier) |
| Frontend | Next.js 14 + recharts |
| Testes | Pytest (99 testes) |

## Começar rápido

```bash
# 1. Clonar
git clone https://github.com/anomalyco/cd-price-tracker.git
cd cd-price-tracker

# 2. Python
pip install -r scraper/requirements.txt
playwright install chromium

# 3. Frontend
cd frontend && npm install

# 4. Variáveis de ambiente
cp scraper/.env.example scraper/.env
cp frontend/.env.example frontend/.env.local
# Preencha SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY, LASTFM_API_KEY...
```

### Criar as tabelas no Supabase

Execute o schema SQL em `supabase/schema.sql` + `supabase/rls.sql` no SQL Editor do Supabase.

### Rodar os testes

```bash
pytest tests/ -v    # 99 testes
```

### Scraping manual

```bash
python -m scraper.main
```

### Painel local

```bash
cd frontend && npm run dev
# Acesse http://localhost:3000
```

## Projeto em árvore

```
cd-price-tracker/
├── scraper/               # Python — scrapers e pipeline
│   ├── main.py            # Orquestrador semanal
│   ├── amazon.py          # Scraper Amazon (com busca automática)
│   ├── mercadolivre.py    # Scraper Mercado Livre
│   ├── shopee.py          # Scraper Shopee (API + fallback)
│   ├── filter.py          # Filtro anti-fanmade
│   ├── price_parser.py    # Normalização de preços BRL
│   ├── models.py          # Dataclasses
│   ├── supabase_client.py # Cliente Supabase
│   ├── alert.py           # Alerta de falha
│   └── email_digest.py    # Digest semanal
├── frontend/              # Next.js 14 App Router
│   ├── app/
│   │   ├── page.tsx            # Home — lista de CDs
│   │   ├── produto/[id]        # Detalhe + gráfico
│   │   ├── cadastro/           # Inscrição email
│   │   ├── gerenciar/          # Admin (listar, adicionar, remover)
│   │   └── api/                # API routes
│   └── components/
│       ├── price-card.tsx      # Card de preço
│       ├── price-chart.tsx     # Gráfico recharts
│       ├── album-search.tsx    # Busca com chips de artista
│       └── platform-form.tsx   # Seleção de lojas
├── seed/                  # Dados de exemplo + validação Last.fm
├── supabase/              # Schema SQL + RLS + seed
├── tests/                 # 99 testes unitários (pytest)
└── .github/workflows/     # GitHub Actions (cron semanal)
```

## Testes

```
99 passed in 114s
```

Cada scraper tem testes mockados (Playwright, httpx). Nenhuma chamada externa real nos testes.

| Testes em destaque | O que cobre |
|---|---|
| `test_amazon.py` | `_normalize`, `_token_similarity`, scrape/search mockados |
| `test_main.py` | `auto_search_query`, `choose_lowest_price`, `persist_result` |
| `test_shopee.py` | API + fallback Playwright |
| `test_filter.py` | 16 casos de fanmade detection parametrizados |

## Próximos passos

Veja [TODO.md](TODO.md) para a lista completa de tarefas planejadas.

## Licença

MIT
