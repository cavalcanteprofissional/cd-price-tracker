# Changelog

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
