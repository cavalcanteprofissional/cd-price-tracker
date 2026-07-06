# 💿 CD Price Tracker

Acompanhe os preços de CDs em Amazon, Mercado Livre e Shopee sem esforço. Scraping automático, histórico em gráfico, e painel web pra gerenciar tudo.

```
     Amazon     Mercado Livre     Shopee
         \           |           /
          \          |          /
       ┌───────────────────────────┐
       │   Scrapers (Playwright)   │ ← todo dia 09:00 BRT
       └───────────┬───────────────┘
                   │
          ┌────────▼────────┐
          │   Supabase DB   │ ← preços + logs
          └──┬──────────┬───┘
             │          │
    ┌────────▼──┐  ┌────▼────────┐
    │  Next.js  │  │ Email       │
    │  painel   │  │ digest      │
    └───────────┘  └─────────────┘
```

## ✨ O que tem aqui

- **Scrapers automáticos** — o sistema descobre os produtos sozinho. Sem URL manual.
- **Amazon** ✅ funcionando | **ML/Shopee** ❌ bloqueados por anti-bot (progresso abaixo)
- **Admin panel** protegido por token — adiciona CDs buscando no Last.fm
- **Histórico de preços** com gráfico interativo (Recharts)
- **Logs de scraping** pra saber o que aconteceu em cada execução
- **Testes**: 99 testes mockados, zero chamadas externas

## 🚀 Rápido

```bash
# Python
pip install -r scraper/requirements.txt
playwright install chromium

# Frontend
cd frontend && npm install

# .env
cp scraper/.env.example scraper/.env
cp frontend/.env.example frontend/.env.local
# Preencha SUPABASE_URL, keys, etc.

# Rodar
pytest tests/ -v           # 99 testes
python scraper/main.py      # scrape manual
cd frontend && npm run dev  # http://localhost:3000
```

## 🖥️ Páginas

| Rota | O que faz |
|---|---|
| `/` | Home com cards dos CDs e último preço |
| `/produto/[id]` | Detalhe do CD com gráfico do histórico |
| `/gerenciar` | Lista CDs, botão pra remover |
| `/gerenciar/adicionar` | Busca álbum no Last.fm, escolhe lojas, salva |
| `/gerenciar/logs` | Logs de cada execução do scraper |

### Busca de álbuns

Digita qualquer coisa — "Thriller", "Michael Jackson", ou os dois. Aparecem capa + artista. Clica nos chips de artista pra filtrar na hora.

```
🔍 Buscar álbum ou artista...

Filtrar por artista: [Michael Jackson] [Pink Floyd]

6 resultados encontrados
```

## 📦 Stack

| Camada | Tecnologia |
|---|---|
| Scraper | Python + Playwright + playwright-stealth |
| Agendamento | GitHub Actions (cron semanal) |
| Banco | Supabase (free tier) |
| Frontend | Next.js 14 + Recharts |
| Testes | Pytest (99 testes) |

## 📁 Estrutura

```
cd-price-tracker/
├── scraper/               # Python
│   ├── main.py            # Orquestrador
│   ├── amazon.py          # Amazon (busca automática)
│   ├── mercadolivre.py    # ML (API + Playwright)
│   ├── shopee.py          # Shopee (API + Playwright)
│   ├── filter.py          # Anti-fanmade
│   ├── price_parser.py    # R$ 49,90 → 49.90
│   ├── alert.py           # Alerta de falha
│   └── email_digest.py    # Digest semanal
├── frontend/              # Next.js 14
│   ├── app/
│   │   ├── page.tsx              # Home
│   │   ├── produto/[id]          # Detalhe + gráfico
│   │   ├── gerenciar/            # Admin
│   │   └── api/                  # API routes
│   └── components/
├── supabase/              # Schema SQL + RLS + seed
├── tests/                 # 99 testes
└── .github/workflows/     # Cron semanal
```

## 🧪 Testes em destaque

| Arquivo | Cobre |
|---|---|
| `test_amazon.py` | `_normalize`, `_token_similarity`, scrape/search mockados |
| `test_main.py` | `auto_search_query`, `choose_lowest_price`, `persist_result` |
| `test_filter.py` | 16 casos de fanmade detection |
| `test_shopee.py` | API + fallback Playwright |

## 🔧 Status dos scrapers

| Loja | Status | Motivo |
|---|---|---|
| Amazon | ✅ OK | Fallback de seletores se o HTML mudar |
| Mercado Livre | ❌ Bloqueado | Anti-bot agressivo (CAPTCHA + API 403) |
| Shopee | ❌ Bloqueado | API 403 + Playwright não extrai itens |

## 📋 Próximos passos

Veja [TODO.md](TODO.md).

## 📄 Licença

MIT
