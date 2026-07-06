# Changelog

## [0.7.0] — 2026-07-05

### Adicionado

#### Log Viewer — `/gerenciar/logs`
- API route `GET /api/scrape-logs` com service key, filtros por status/platform, paginação
- Página com tabela de logs, filtros dropdown (status + plataforma), badges coloridos
- Link "Logs de Scraping" no `/gerenciar` ao lado de "Adicionar CD"

#### Scrapers — Amazon fallback + ML API
- Amazon: `_extract_candidates()` com fallback `a[href*='/dp/']` para HTML novo da Amazon
- Amazon: múltiplos search terms (`"cd original"` e `"cd"`)
- Amazon: similaridade por artista no texto completo do resultado (score mínimo 0.15)
- Mercado Livre: fallback via API pública `api.mercadolibre.com/sites/MLB/search`
- Shopee: Playwright fallback com `wait_for_selector`, scroll, múltiplos seletores

### Corrigido

#### Cache da Home Page
- `supabase.ts` — `cache: 'no-store'` no fetch do supabase client Server Component
- Dados frescos aparecem imediatamente após adicionar CD via admin

#### Home — Preço agora é link clicável
- `price-card.tsx` — `<span>` do preço substituído por `<a href={listing_url} target="_blank">`
- Abre o anúncio real em nova aba

#### Corrigido hydration error (âncora dentro de âncora)
- `price-card.tsx` — wrapper `<a>` → `<div>` + `useRouter().push()`
- `e.stopPropagation()` no badge de preço para não disparar redirect do card

#### Pipeline — Scraping diário
- GitHub Actions alterado de `0 12 * * 1` (semanal) para `0 12 * * *` (diário, 09:00 BRT)

#### Scrapers — Anti-bot mitigations
- `main.py`: stealth global com `--disable-blink-features=AutomationControlled`, viewport realista, locale pt-BR, timezone SP, geolocation SP, `add_init_script()` anulando `navigator.webdriver`
- `mercadolivre.py`: tenta API pública primeiro, fallback Playwright com log diagnóstico (CAPTCHA detectado)
- `shopee.py`: `wait_until='networkidle'` para SPA carregar completamente; extração de `__INITIAL_STATE__` / `__NEXT_DATA__` / JSON-LD em múltiplas profundidades
- ML e Shopee continuam bloqueados por anti-bot agressivo (CAPTCHA + verificação de tráfego)

#### Produto detalhe — Link "Ver na loja"
- `produto/[id]/page.tsx` — link direto pro anúncio abaixo de cada gráfico de plataforma

### Alterado

#### Scrapers refatorados
- `amazon.py`: `_extract_candidates()` + `_search_amazon_with_query()` separados
- `mercadolivre.py`: API httpx + Playwright fallback em vez de Playwright-only
- `shopee.py`: `_first_selector()` para tentar múltiplos seletores em cada item

## [0.6.0] — 2026-07-05

### Adicionado

#### Busca de Álbuns — Filtro por Artista (chips)
- Input único com ícone 🔍 e placeholder "Buscar álbum ou artista..."
- Chips de artista extraídos dos resultados — clique para filtrar, clique de novo para remover
- Filtro client-side instantâneo (sem nova requisição)
- Contador "X resultados encontrados"
- Chips ocultos quando há somente 1 artista

#### Testes — Bateria completa (16 → 99 testes)
- `test_amazon.py` — `_normalize`, `_token_similarity`, `scrape_amazon` (5 cenários mockados), `search_amazon` (5 cenários mockados)
- `test_mercadolivre.py` — scrape_mercadolivre mockado (5 cenários)
- `test_shopee.py` — `_extract_from_api`, `_extract_from_page`, fallback API→Playwright (10 cenários)
- `test_main.py` — `auto_search_query`, `choose_lowest_price`, `persist_result`
- `test_models.py` — `ScrapedProduct`, `ScrapeResult`
- `test_validate_albums.py` — `_normalize`, `token_similarity`, `_pick_best_image`, `LastFMClient`
- `test_email_digest.py` — renderização HTML do digest
- `test_alert.py` — envio de alerta
- `test_filter.py` — refatorado para `@pytest.mark.parametrize` (16 casos)
- `test_price_parser.py` — refatorado para `@pytest.mark.parametrize` (10 casos)

#### Dependência
- `pytest-mock` — fixture `mocker` para mocks limpos nos testes

### Corrigido

#### Frontend — Cache da Home Page
- `app/page.tsx` adicionado `export const dynamic = "force-dynamic"` — impede Next.js de servir HTML estático em cache
- Logging adicionado nas API routes DELETE e POST para depuração

#### Scrapers — playwright-stealth v2
- `main.py` atualizado de `stealth_sync()` para `Stealth().apply_stealth_sync()` (compatibilidade v2.0.3)

#### Email Digest — Template bug
- `email_digest.py` — `R$` em `Template()` causava `ValueError` (`$` seguido de espaço é inválido). Corrigido com `R$$` (escape)

### Alterado

#### Frontend — Busca de Álbuns
- Removido sistema de dois inputs (álbum + artista separados)
- Substituído por input único + chips de artista pós-busca
- `adicionar/page.tsx` — fix de tipo TypeScript (`token!` no header fetch)

#### API Route
- `/api/albums/search` — removido suporte a `?artist=` (volta ao original, `?q=` apenas)

## [0.5.0] — 2026-07-05

### Alterado

#### Frontend — Formulário de Adicionar simplificado
- `platform-form.tsx` — removidos campos de URL Amazon e search_query ML/Shopee
- Agora só checkboxes: marcar plataforma = sistema descobre automaticamente
- API `/api/albums/add` — aceita array de strings `["amazon", "mercado_livre"]`

#### Scrapers — Busca automática
- `amazon.py` — nova função `search_amazon(title, artist, context)` que:
  - Busca na Amazon por título + artista via Playwright
  - Encontra o melhor resultado por similaridade de texto
  - Extrai preço da página de busca (ou navega ao produto se necessário)
- `main.py` — quando `amazon_url` ou `search_query` são NULL:
  - Amazon: chama `search_amazon` com nome do CD
  - ML/Shopee: auto-gera `{title} {artist} cd original`

#### Seed
- `supabase/seed.sql` — `amazon_url` e `search_query` agora como NULL (auto-descoberta)
- `seed/products.json` e `products_enriched.json` — estrutura simplificada

#### Schema do banco
- Nenhuma tabela removida (schema permanece inalterado)
- `amazon_url` e `search_query` mantidos como nullable
- Dados existentes no Supabase atualizados para NULL

## [0.4.0] — 2026-07-05

### Adicionado

#### Gestão de CDs (Admin Panel)
- `ADMIN_TOKEN` — proteção por token fixo nas API routes
- API `GET /api/albums/search` — proxy de busca no Last.fm
- API `POST /api/albums/add` — adicionar produto + plataformas
- API `DELETE /api/albums/[id]` — remover produto com cascade
- Componente `admin-auth.tsx` — formulário de token com sessionStorage
- Componente `album-search.tsx` — busca Last.fm com debounce 400ms
- Componente `platform-form.tsx` — checkboxes Amazon/ML/Shopee + campos condicionais
- Página `/gerenciar` — listagem dos CDs com botão remover
- Página `/gerenciar/adicionar` — busca + seleção + plataformas + salvar
- Link "Gerenciar" na nav bar

## [0.3.0] — 2026-07-05

### Adicionado

#### Infraestrutura (Supabase)
- Projeto Supabase free tier criado
- `supabase/schema.sql` — arquivo SQL com CREATE TABLEs + índices
- `supabase/rls.sql` — arquivo SQL com RLS policies
- `supabase/seed.sql` — INSERTs dos 5 CDs enriquecidos com metadados Last.fm
- Schema + RLS + seed aplicados no Supabase via MCP
- Variáveis de ambiente configuradas localmente

## [0.2.0] — 2026-07-05

### Adicionado

#### Validação de Álbuns (Last.fm API)
- `seed/validate_albums.py` — script de validação e enriquecimento de álbuns via Last.fm API
  - Busca cada CD do seed via `album.search` + `album.getInfo`
  - Score de similaridade (token overlap) para match inteligente
  - Enriquece com `lastfm_url`, `release_date`, `genre` (top 5 tags), `cover_url`, `lastfm_listeners`
  - Gera `seed/products_enriched.json` com dados validados
  - Loga warnings para álbuns não encontrados ou baixa confiança

#### Schema do banco
- Novas colunas na tabela `products`: `lastfm_url`, `release_date`, `genre`, `lastfm_listeners`

#### Configuração
- Variável `LASTFM_API_KEY` nos `.env.example`

#### Documentação
- Passo a passo de obtenção da API Key do Last.fm no skill
- Seção de validação de álbuns no skill

## [0.1.0] — 2026-07-03

### Adicionado

#### Scraper Python
- `filter.py` — filtro anti-fanmade com 13 padrões regex para detectar CDs caseiros, fanmade, bootleg, etc.
- `price_parser.py` — normalização de preços brasileiros (ex: `R$ 49,90` → `49.90`, `R$ 1.234,56` → `1234.56`)
- `models.py` — dataclasses `ScrapedProduct` e `ScrapeResult` para tipagem dos dados
- `supabase_client.py` — cliente Supabase com service_role key para escrita no banco
- `alert.py` — notificação de falha do pipeline via Resend
- `amazon.py` — scraper da Amazon com Playwright + playwright-stealth + seletores CSS
- `mercadolivre.py` — scraper do Mercado Livre com busca textual + extração de resultados
- `shopee.py` — scraper da Shopee via API interna (`/api/v4/search/search_items`) com fallback para Playwright
- `main.py` — orquestrador completo com retry exponencial (tenacity), logging estruturado, persistência em Supabase e envio de digest
- `email_digest.py` — template HTML para o digest semanal com variação de preço e link de unsubscribe

#### Testes
- `tests/test_filter.py` — 11 testes unitários para o filtro anti-fanmade
- `tests/test_price_parser.py` — 5 testes unitários para o parser de preço
- **16/16 testes passando**

#### Frontend (Next.js 14 + App Router)
- `app/page.tsx` — página inicial com grid de CDs e último preço por plataforma
- `app/produto/[id]/page.tsx` — página de detalhe com gráfico recharts do histórico
- `app/cadastro/page.tsx` — formulário de cadastro de email
- `app/api/subscribe/route.ts` — API route de inscrição com geração de tokens
- `app/api/confirm/route.ts` — API route de confirmação (double opt-in)
- `app/api/unsubscribe/route.ts` — API route de cancelamento com token
- `components/price-card.tsx` — card reutilizável de exibição de preço
- `components/price-chart.tsx` — gráfico recharts com variação no período
- `components/subscribe-form.tsx` — formulário com estado loading/success/error
- `lib/supabase.ts` — cliente Supabase anon key para Server Components

#### Devops
- `.github/workflows/weekly-scrape.yml` — GitHub Actions com cron semanal (seg 09:00 BRT), timeout 30min, execução de testes antes do scrape
- `seed/products.json` — seed de 5 CDs de exemplo (Michael Jackson, Beatles, Pink Floyd, Nirvana, Radiohead)

#### Documentação
- `cd-price-tracker-skill.md` — documento completo de arquitetura e especificação
- `README.md` — visão geral do projeto
- `TODO.md` — plano de tarefas pendentes
- `CHANGELOG.md` — este arquivo

### Configuração
- `requirements.txt` — dependências Python (playwright, playwright-stealth, supabase, httpx, tenacity, pytest, resend)
- `package.json` — dependências Next.js (next, react, recharts, @supabase/supabase-js, resend)
- `tsconfig.json` — configuração TypeScript estrita
- `next.config.js` — remotePatterns para imagens externas
- `.env.example` — templates de variáveis de ambiente
- `.python-version` — Python 3.12
- `.gitignore` — node_modules, .next, __pycache__, .env
