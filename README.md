# 💿 CD Price Tracker <sup><sub>v0.9.14</sub></sup>

Acompanhe os preços dos seus CDs favoritos em várias lojas brasileiras. Scraping automático todo dia, histórico em gráfico, e um painel pra você gerenciar sua coleção.

```mermaid
flowchart TB
    subgraph Schedule["⏰ GitHub Actions (09:00 BRT)"]
        CRON["cron(0 12 * * *)"]
        TRIGGER["⏺ Botão ▶ Rodar (navbar)"]
    end

    subgraph Scrapers["🕷️ Scrapers (Python + Playwright)"]
        AMZN["Amazon BR ✅"]
        AMZN_US["Amazon US ✅"]
        AMZN_UK["Amazon UK ✅"]
        AMZN_DE["Amazon DE ✅"]
        ML["Mercado Livre ❌"]
        SHOP["Shopee ❌"]
        MGL["Magazine Luiza ❌"]
        ENJ["Enjoei ⚠️"]
    end

    subgraph LastFM["🎵 Last.fm API"]
        SEARCH["Buscar álbum"]
        VALIDATE["Validar metadados"]
    end

    subgraph Supabase["🗄️ Supabase DB"]
        PRODUCTS["products"]
        CONFIG["product_platform_config"]
        PRICES["price_history"]
        LOGS["scrape_log"]
        SUBS["subscribers"]
    end

    subgraph Frontend["🌐 Next.js 14"]
        HOME["/ — Home"]
        DETAIL["/produto/[id] — Gráfico + Platform Manager"]
        ADMIN["/gerenciar — Admin"]
        ADD["/gerenciar/adicionar — todas as lojas marcadas"]
        LOGS_PAGE["/gerenciar/logs"]
        NAV["Navbar: ▶ Rodar (live logs)"]
    end

    subgraph Email["📧 Email (Resend)"]
        DIGEST["Digest semanal"]
        ALERT["Alerta de falha"]
    end

    CRON --> Scrapers
    TRIGGER --> Scrapers
    Scrapers --> Supabase
    LastFM --> Frontend
    Supabase --> Frontend
    Frontend --> Email
    Scrapers --> Email
```

## ✨ O que você pode fazer

- **Ver os preços** dos seus CDs na página inicial — Amazon (BR/US/UK/DE), Mercado Livre, Shopee, tudo num lugar só
- **Clicar no preço** pra ir direto pro anúncio na loja
- **Ver o histórico** de cada CD em gráfico — subiu? caiu? na média?
- **Adicionar CDs** buscando pelo nome ou artista — o Last.fm encontra a capa, ano, gênero
- **Escolher as lojas** que quer monitorar — o sistema descobre o produto sozinho, sem você digitar URL (todas marcadas por padrão)
- **Editar as lojas** de um CD já cadastrado direto na página de detalhe
- **Rodar o scraping na hora** com o botão ▶ Rodar no navbar e ver os logs ao vivo
- **Consultar os logs** de cada execução do scraper — deu certo? falou? por quê?

## 🚀 Como começar

```bash
# Python
pip install -r scraper/requirements.txt
playwright install chromium

# Frontend
cd frontend && npm install

# .env
cp scraper/.env.example scraper/.env.local
cp frontend/.env.example frontend/.env.local
# Preencha SUPABASE_URL, SERVICE_KEY, ADMIN_TOKEN, etc.

# Testar
pytest tests/ -v

# Rodar o scraper manualmente
python -m scraper.main

# Ou via script direto (mesma coisa)
cd scraper && python main.py

# Iniciar o painel web
cd frontend && npm run dev
# Abre em http://localhost:3000
```

## 🖥️ Páginas

| Rota | O que faz |
|---|---|
| `/` | Home — grid dos CDs com o último preço de cada loja |
| `/produto/[id]` | Detalhe do CD + gráfico do histórico + gerenciar lojas |
| `/gerenciar` | Lista os CDs cadastrados, com botão pra remover |
| `/gerenciar/adicionar` | Busca álbum no Last.fm, escolhe as lojas (todas marcadas), salva |
| `/gerenciar/logs` | Tabela com logs de cada execução (status, plataforma, erro) |

### Busca de álbuns

Digita qualquer coisa — "Thriller", "Michael Jackson", ou os dois juntos. O Last.fm devolve os resultados com capa e artista. Depois da busca, aparecem **chips de artista** pra filtrar na hora.

```
🔍 Buscar álbum ou artista...

Filtrar por artista: [Michael Jackson] [Pink Floyd] [Radiohead]

6 resultados encontrados
```

## 🔧 Status dos scrapers

| Loja | Scraper | Status | Extrator |
|---|---|---|---|
| Amazon BR | `amazon.py` | ✅ Funcionando | Playwright + busca automática + fallback de seletores |
| Amazon US | `amazon_global.py` | ✅ Funcionando | Playwright, domínio `.com`, moeda USD |
| Amazon UK | `amazon_global.py` | ✅ Funcionando | Playwright, domínio `.co.uk`, moeda GBP, penalidade de álbum |
| Amazon DE | `amazon_global.py` | ✅ Funcionando | Playwright, domínio `.de`, moeda EUR, penalidade de álbum |
| Enjoei | `enjoei.py` | ⚠️ Instável | API GraphQL + Playwright DOM + page.evaluate() — 3 estratégias em cascata |
| Mercado Livre | `mercadolivre.py` | ❌ Bloqueado | CAPTCHA Akamai + API OAuth pendente |
| Shopee | `shopee.py` | ❌ Bloqueado | Redireciona pra verificação de tráfego |
| Mag. Luiza | `magalu.py` | ❌ Bloqueado | Akamai 403 na primeira requisição |

**Resumo:** Amazon BR + Global funcionam 100%. Enjoei em desenvolvimento com 3 estratégias de extração em cascata (API → DOM → evaluate). As demais lojas brasileiras usam anti-bot pesado (Akamai, DataDome) que bloqueia até Playwright com stealth. Plano futuro: **API oficial Mercado Livre** (OAuth) e **Google Shopping API** como fontes alternativas.

## 📦 Stack

| Camada | Tecnologia |
|---|---|
| Scrapers | Python + Playwright + playwright-stealth |
| Agendamento | GitHub Actions (todo dia às 09:00 BRT) |
| Banco de dados | Supabase (free tier — Postgres + RLS + API) |
| Validação de álbuns | Last.fm API |
| Frontend | Next.js 14 (App Router) + Recharts |
| Testes | Pytest (73 unit + 25 mock = 99 testes) |
| Notificações | Resend (futuro) |

## 📁 Estrutura do projeto

```
cd-price-tracker/
├── scraper/               # Python — tudo que roda o scraping
│   ├── main.py            # Orquestrador — coordena tudo
│   ├── amazon.py          # Amazon BR ✅ funcionando
│   ├── amazon_global.py   # Amazon US/UK/DE ✅ funcionando
│   ├── mercadolivre.py    # ML ❌ bloqueado (fallback)
│   ├── mercadolivre_api.py# ML API oficial OAuth ⏳ pendente
│   ├── shopee.py          # Shopee ❌ bloqueado
│   ├── magalu.py          # Magalu ❌ bloqueado
│   ├── enjoei.py          # Enjoei ⚠️ instável (API + DOM + evaluate)
│   ├── filter.py          # Filtro anti-fanmade
│   ├── utils.py           # normalize, token_similarity, first_selector, best_match
│   ├── price_parser.py    # "R$ 49,90" → 49.90
│   ├── alert.py           # Alerta de falha no pipeline
│   └── email_digest.py    # Digest com variação de preços
├── frontend/              # Next.js 14
│   ├── app/
│   │   ├── page.tsx               # Home
│   │   ├── produto/[id]           # Detalhe + gráfico + platform manager
│   │   ├── gerenciar/             # Admin
│   │   ├── api/                   # API routes
│   │   │   ├── scrape/trigger     # POST ▶ Rodar
│   │   │   └── albums/[id]/platforms  # PATCH gerenciar lojas
│   │   └── layout.tsx             # Navbar com ▶ Rodar
    │   ├── components/
    │   │   ├── scrape-button.tsx      # Botão ▶ Rodar + live logs
    │   │   ├── platform-manager.tsx   # Gerenciar lojas do CD
    │   │   ├── platform-form.tsx      # Formulário de adicionar (todas marcadas)
    │   │   ├── album-search.tsx       # Busca Last.fm
    │   │   ├── admin-auth.tsx         # Login admin
    │   │   ├── error-boundary.tsx     # ErrorBoundary classe
    │   │   ├── price-card.tsx         # Card de preço
    │   │   └── price-chart.tsx        # Gráfico recharts
    │   └── lib/
    │       └── platforms.ts          # ALL_PLATFORMS, labels, icons, badges
├── supabase/              # SQL do banco
├── tests/                 # 99 testes mockados
└── .github/workflows/     # CI/CD
```

## 📊 Dashboard

Na home você vê o grid completo dos CDs com o último preço de cada loja:

```
┌──────────────────────────────────────────┐
│  💿  Thriller                            │
│      Michael Jackson                     │
│                                          │
│  🇧🇷 Amazon BR    R$ 44,90  🛒           │
│  🇺🇸 Amazon US    $ 12,95   🛒           │
│  🇬🇧 Amazon UK    £ 11,20   🛒           │
│  🇩🇪 Amazon DE    € 13,40   🛒           │
│  🟡 Mercado Livre  —  sem preço          │
│  🛍️ Shopee        R$ 39,90  🛒          │
│  💛 Enjoei        R$ 52,00  🛒          │
└──────────────────────────────────────────┘
```

**Clique no preço** → abre o anúncio direto na loja.  
**Clique no card** → abre página de detalhe com gráfico do histórico + gerenciamento de plataformas.

Na navbar, o botão **▶ Rodar** executa o scraper na hora com logs ao vivo via SSE — sem precisar esperar o cron diário.

## 🧪 Testes

**73 testes unitários** + 25 testes com Playwright mockado (99 total). Zero chamadas externas. Tudo mockado com pytest-mock.

| Arquivo | O que testa |
|---|---|
| `test_amazon.py` | `_normalize`, `_token_similarity`, `scrape_amazon` (5 cenários), `search_amazon` (5) |
| `test_main.py` | `auto_search_query`, `choose_lowest_price`, `persist_result` |
| `test_filter.py` | 16 casos de fanmade detection |
| `test_shopee.py` | API + fallback Playwright |
| `test_mercadolivre.py` | API + Playwright fallback |
| `test_models.py` | Dataclasses `ScrapedProduct` e `ScrapeResult` |
| `test_price_parser.py` | 11 formatos de preço brasileiro (inclui `None`) |
| `test_utils.py` | normalize, token_similarity, first_selector, best_match |
| `test_email_digest.py` | Renderização do template HTML |
| `test_alert.py` | Envio de alerta por email |
| `test_validate_albums.py` | Last.fm client, score, imagem |

## 🔭 O que vem por aí

A Amazon funciona 100% (BR + US + UK + DE). O foco agora é destravar as lojas bloqueadas:

1. **API oficial do Mercado Livre** — app registrado, aguardando aprovação (OAuth). Se funcionar, resolve ML sem browser.
2. **Google Shopping API** — fonte agregada que cobre várias lojas numa chamada só.
3. **VPS com browser headful** — rodar Playwright com janela visível pra lojas com Akamai.
4. **Buscapé / Zoom** — comparadores que podem listar preços das lojas bloqueadas.

Veja o [TODO.md](TODO.md) completo.

## 📄 Licença

MIT — usa, modifica, compartilha.
