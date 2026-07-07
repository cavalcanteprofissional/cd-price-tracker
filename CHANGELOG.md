# Changelog

## [0.9.9] — 2026-07-07

### Adicionado

#### Streaming SSE em tempo real (modo local)
- `trigger/route.ts` — `POST /api/scrape/trigger` reescrito com `spawn` + `TransformStream` + SSE (`text/event-stream`)
- `scrape-button.tsx` — `handleClick` detecta `content-type: text/event-stream` e lê o `ReadableStream` diretamente
- Live status aparece como **entry única ℹ️** no topo do painel, substituída a cada evento — sem acumular
- Resultados estruturados (success/error/not_found) são buscados via **polling em paralelo** durante o streaming, empilhados em tempo real
- Abort handler no servidor mata o processo filho quando o cliente desconecta
- Flag `writerClosed` + `safeSse()` para evitar `ERR_INVALID_STATE` em chunks tardios de stdout/stderr

#### Botão de conclusão com resumo
- Botão mostra `✅ 5 · 2 ⚠️ · 1 ⚪` ao concluir (com fundo verde, ou âmbar se só erros)
- Banner `🎉` no painel: "5 encontrados · 2 erros · 1 não encontrado · 35s"

#### Textos amigáveis nos logs
- Linha 2 sempre inicia com a palavra em português: `encontrado`, `não encontrado`, `erro`, `fanmade ignorado`
- `not_found` não mostra detail redundante ("sem resultados")
- `success` mostra ` → {raw_title}` só quando agrega info nova
- Live status limpa prefixo `timestamp [LEVEL] module:` dos logs Python

### Corrigido

#### `writerClosed = true` antes de `safeSse()` — eventos done/error nunca chegavam
- `trigger/route.ts` — nos handlers `close` e `error`, a flag `writerClosed` era setada **antes** de `safeSse()`, fazendo o cliente nunca receber os eventos de conclusão
- Status ficava `"running"` até o safety reset de 30s forçar `idle`; botão nunca exibia ✅
- Corrigido: `writerClosed = true` movido para **após** `safeSse()` em ambos os handlers

#### Perda de estado ao navegar para `/gerenciar/logs`
- `gerenciar/page.tsx` — `<a href="/gerenciar/logs">` substituído por `<Link>` (causava full page reload, desmontando o layout e perdendo todo estado React)
- `gerenciar/logs/page.tsx` — `<a href="/gerenciar">` (Voltar) substituído por `<Link>`

### Alterado

#### Simplificação da persistência em sessionStorage
- 5 `useEffect` de save (status, panelOpen, startedAt, mode, errorMessage) fundidos em **1 único** `useEffect` que serializa tudo num JSON blob
- Restauração lê o JSON no lugar de 6 chaves individuais
- Polling não escreve mais `lastUpdateAt`/`knownIds` separadamente
- Código mais enxuto e menos propenso a race conditions

#### Computados movidos para `useMemo`
- `btnText`, `btnBg`, `successCount`, `errorCount`, `notFoundCount` agora usam `useMemo` com dependências explícitas
- Hooks movidos para **antes** do `if (!token) return null` (rules of hooks)

### Observação
- README não necessita atualização — a arquitetura já descreve "Navbar: ▶ Rodar (live logs)"

### Corrigido

#### Hydration error: sessionStorage no SSR + race condition nos save effects
- `scrape-button.tsx` — `useState`/`useRef` voltaram a usar valores **default** para garantir match SSR ↔ hidratação
- `isFirstRender` ref adicionado — **save effects pulam no primeiro ciclo**, evitando o race condition que sobrescrevia o sessionStorage com valores iniciais antes do restore rodar
- `useEffect` de restore roda depois dos save effects: restaura `status`, `startedAt`, `mode`, `errorMessage`, `panelOpen`, `knownIds`, `lastUpdateAt` do sessionStorage e só então desmarca `isFirstRender`
- Após o restore, save effects passam a funcionar normalmente, persistindo o estado restaurado

### Alterado
- Polling continua salvando `lastUpdateAt` e `knownIds` no sessionStorage a cada lote de logs
- `handleClick` salva `lastUpdateAt` e limpa `knownIds` no início de um novo scrape

## [0.9.7] — 2026-07-07

### Corrigido

#### `ReferenceError: sessionStorage is not defined` no SSR
- `scrape-button.tsx` — todo acesso a `sessionStorage` nos inicializadores de `useState`/`useRef` agora é envolto em `try/catch`
- Durante SSR (Server-Side Rendering), `sessionStorage` não existe no Node.js; os inicializadores retornam o valor default silenciosamente
- No cliente, o estado é restaurado normalmente

## [0.9.6] — 2026-07-07

### Corrigido

#### Botão "▶ Rodar" e painel de logs resetavam ao navegar entre páginas
- `scrape-button.tsx` — `useState` e `useRef` agora são inicializados **lendo diretamente do sessionStorage** via função inicializadora, em vez de restaurar via `useEffect`
- Removeu o `useEffect` de restore que causava **race condition**: os save effects rodavam com valores iniciais (`"idle"`, `false`) antes do restore effect atualizar, sobrescrevendo o estado salvo
- Estado persiste corretamente entre navegações: `status`, `startedAt`, `mode`, `errorMessage`, `panelOpen`, `knownIds`, `lastUpdateAt`
- Polling retoma automaticamente se `status` era `"running"`

## [0.9.5] — 2026-07-07

### Corrigido

#### ADMIN_TOKEN com caractere `#` interpretado como comentário
- `.env.local` — token alterado de `HonkaiImpact3rd@#` para `HonkaiImpact3rd` (removeu `#` que era interpretado como início de comentário pelo parser de `.env`, truncando o valor)
- `trigger/route.ts` — adicionado logging detalhado no mismatch do token (comprimentos recebido vs esperado)
- `scrape-logs/route.ts` — mesmo logging adicionado

### Adicionado

#### Endpoint de diagnóstico GET /api/scrape/trigger
- `trigger/route.ts` — novo handler `GET` que retorna os tokens recebido vs esperado (mascarado: length, primeiro/último caractere) para debug rápido de 401
- Uso: `curl -H "x-admin-token: SEU_TOKEN" http://localhost:3000/api/scrape/trigger`

## [0.9.4] — 2026-07-07

### Corrigido

#### POST /api/scrape/trigger retornava 401 no Windows
- `trigger/route.ts` — `process.env.ADMIN_TOKEN` agora com `.trim()` para remover `\r` residual de arquivos `.env` com CRLF no Windows
- `scrape-logs/route.ts` — mesma correção no `ADMIN_TOKEN` para consistência

#### Exec do scraper falhava silenciosamente
- `trigger/route.ts` — adicionado pre-check `python --version` antes de spawnar o scraper; se Python não estiver disponível, retorna 500 com mensagem clara
- `trigger/route.ts` — se o `exec` falhar (processo não iniciou), escreve logs de erro no Supabase para cada config ativa, permitindo que o frontend detecte via polling

### Alterado
- `trigger/route.ts` — adicionado import do `createClient` do Supabase para fallback de logging

## [0.9.3] — 2026-07-06

### Corrigido

#### Botão "▶ Rodar" virava ❌ sem feedback
- `scrape-button.tsx` — painel não abria no estado `error`; adicionado `"error"` à condição de visibilidade
- `scrape-button.tsx` — erro do `POST /api/scrape/trigger` agora é capturado e exibido no cabeçalho do painel
- `scrape-button.tsx` — botão mostra "❌ Tentar novamente" em vez de apenas ❌
- `trigger/route.ts` — corpo inteiro envolvido em `try/catch` com logging para diagnosticar exceções na rota

## [0.9.2] — 2026-07-06

### Corrigido

#### Exception não tratada no search_amazon (Playwright timeout)
- `scraper/amazon.py` — `_search_amazon_with_query()` tinha `try/finally` sem `except`; exceções como timeout do Playwright propagavam sem tratamento
- Adicionado `except Exception` que loga o erro e retorna `None`, consistente com o padrão de `scrape_amazon()`
- Teste `test_exception_handled` passou a falhar; corrigido com o bloco except

## [0.9.1] — 2026-07-06

### Adicionado

#### Plataformas no dispatch do main.py
- `main.py` — handlers explícitos para `americanas`, `casas_bahia`, `submarino`, `carrefour`, `extra` com log "Scraper nao implementado" em vez de "Plataforma desconhecida"

### Corrigido

#### Parse de preço internacional (UK/DE)
- `price_parser.py` — adicionado `£€` à regex de remoção de símbolos monetários
- `price_parser.py` — adicionado `re.sub(r"[^\d,.\-]", "", text)` para remover lixo não numérico (ex: `BL82.73` → `82.73`)

#### Matching Amazon Global (UK/DE)
- `amazon_global.py` — novo sistema de score que **penaliza candidatos sem o token do álbum** no título
  - Extrai tokens exclusivos do álbum (ex: `lungs`) subtraindo tokens do artista (`florence`, `the`, `machine`)
  - Aplica penalidade 0.3× se o token do álbum estiver ausente
  - Adicionado terceiro termo de busca `f"{title} {artist}"` (sem sufixo) pra aumentar cobertura

## [0.9.0] — 2026-07-06

### Adicionado

#### Run Scraper — Botão no Navbar com Live Logs
- `frontend/app/api/scrape/trigger/route.ts` — `POST /api/scrape/trigger` com exec local (`python -m scraper.main`) e dispatch GitHub Actions (Vercel)
- `frontend/components/scrape-button.tsx` — botão "▶ Rodar" no navbar que abre painel flutuante
- Live log feed com polling a cada 3s (`GET /api/scrape-logs?since=X`)
- Auto-stop após 5 minutos sem logs novos; indicador "📡 Xs sem atualização"
- Polling persiste entre navegações (layout não desmonta)
- Filtro `?since=` adicionado ao `GET /api/scrape-logs`

#### Platform Manager — Editar lojas no detalhe do CD
- `frontend/app/api/albums/[id]/platforms/route.ts` — `PATCH` que sincroniza plataformas (deleta removidas, insere novas)
- `frontend/components/platform-manager.tsx` — checkboxes com admin auth via sessionStorage
- Integrado em `/produto/[id]` abaixo dos gráficos
- Labels de plataforma no `/gerenciar` expandidas (BR, US, UK, DE, ML, MGL, AM, CB, SP)

#### Todas as lojas marcadas por default no cadastro
- `frontend/components/platform-form.tsx` — `useState` inicializado com todas as plataformas
- Removeu a necessidade de selecionar uma a uma ao adicionar CD

### Corrigido

#### Scraper via botão
- `trigger/route.ts`: `exec` usa `python -m scraper.main` com `cwd` na raiz (resolve `ModuleNotFoundError`)
- `exec` mapeia `SUPABASE_URL` de `NEXT_PUBLIC_SUPABASE_URL` (resolve `KeyError`)
- Live log: removido auto-timeout de 60s que impedia logs de aparecerem

#### Platform Manager — CHECK constraint
- Identificado que migrações via MCP foram parar em projeto Supabase diferente do real
- Script de recuperação fornecido para aplicar constraint expandido no projeto correto

### Documentação
- `CHANGELOG.md` — v0.9.0 completo
- `TODO.md` — seções Run Scraper + Platform Manager + correções
- `frontend/.env.example` — adicionado `GITHUB_PAT`, `GITHUB_OWNER`, `GITHUB_REPO`

## [0.8.0] — 2026-07-05

### Adicionado

#### Expansão de plataformas — Schema + Frontend
- CHECK constraint do `product_platform_config` expandido com 6 novas plataformas: `magalu`, `americanas`, `casas_bahia`, `submarino`, `carrefour`, `extra`
- `frontend/components/platform-form.tsx` — checkboxes para Magalu, Americanas, Casas Bahia
- `frontend/components/price-card.tsx` — labels para todas as novas plataformas
- `supabase/seed.sql` — configs Magalu + Americanas para o CD Thriller

#### Scraper Magazine Luiza
- `scraper/magalu.py` — Playwright + `wait_until='networkidle'` + detecção de bloqueio Akamai
- Registrado em `main.py` via `_process_platform_scrape()`, mesmo padrão de ML/Shopee
- Funções auxiliares: `_extract_from_page()`, `_best_match()`, `_first_selector()`

### Alterado

#### README refeito
- Diagrama de arquitetura em Mermaid no topo
- Tom mais amigável e direto ao ponto
- Status dos scrapers atualizado com Magalu
- Stack, estrutura, e próximos passos revisados

#### CHANGELOG reorganizado
- Seções "Adicionado", "Corrigido", "Alterado" com marcadores descritivos
- v0.8.0 com detalhes completos da expansão

### Observação

Magalu testado e bloqueado por Akamai 403 — mesma proteção anti-bot de Mercado Livre e Shopee. Todas as lojas brasileiras grandes usam anti-bot agressivo. Plano revisado no TODO.md: Google Shopping API como próxima alternativa.

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
