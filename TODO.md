# TODO — CD Price Tracker

## Plano geral de expansão (sem custo)

### 🟢 Fase 1 — API oficial Mercado Livre (prioridade máxima)
| Tarefa | Status |
|---|---|
| Criar `scraper/mercadolivre_api.py` com OAuth client | ✅ Feito |
| Adicionar `ML_APP_ID` e `ML_CLIENT_SECRET` no `.env.example` | ✅ Feito |
| Atualizar `mercadolivre.py` para usar API client autenticado | ✅ Feito |
| Registrar app em `developers.mercadolivre.com.br` | 🔄 Pendente (usuário) |
| Preencher credenciais + testar | ❌ |
| Se funcionar, remover fallback Playwright | ❌ |

### 🟢 Fase 2 — Amazon Global
| Tarefa | Status |
|---|---|
| Criar `scraper/amazon_global.py` com marketplaces US/UK/DE | ✅ Feito |
| Adicionar `amazon_us`, `amazon_uk`, `amazon_de` ao CHECK constraint | ✅ Feito |
| Atualizar `main.py` com `process_amazon_global()` | ✅ Feito |
| Atualizar frontend (PlatformForm + PriceCard) | ✅ Feito |
| Testar Amazon US com Playwright | ❌ |

### 🟡 Fase 4 — xvfb-run no GitHub Actions
| Tarefa | Status |
|---|---|
| Atualizar workflow para usar `xvfb-run` | ✅ Feito |
| Testar se Akamai libera com headful virtual no GHA | ❌ |

### 🟡 Fase 3 — Google Shopping API
| Tarefa | Status |
|---|---|
| Criar Google Cloud Project | 🔄 Pendente (usuário) |
| Habilitar Shopping API | ❌ |
| Criar `scraper/googleshopping.py` | ❌ |
| Integrar em `main.py` | ❌ |

### 🟠 Fase 5 — Firefox em vez de Chromium
| Tarefa | Status |
|---|---|
| Testar Firefox nos scrapers bloqueados | ✅ Testado |
| Resultado: ML passou do CAPTCHA (caiu em verificação de conta), Magalu/Shopee continuam bloqueados | ✅ Documentado |

### 🟠 Fase 6 — SerpAPI (Google Shopping alternativo)
| Tarefa | Status |
|---|---|
| Criar conta SerpAPI (100 buscas/mês grátis) | 🔄 Pendente (usuário) |
| Criar `scraper/serpapi.py` | ❌ |
| Integrar em `main.py` | ❌ |

### 🔴 Fase 7 — Comparadores brasileiros (Buscapé/Zoom)
| Tarefa | Status |
|---|---|
| Testar Buscapé com Playwright | ❌ |
| Testar Zoom com Playwright | ❌ |
| Se funcionar, criar scraper e integrar | ❌ |

---

## 0. Validação de Álbuns (Last.fm API)

- [x] Criar conta no Last.fm e gerar API Key
- [x] `seed/validate_albums.py` — valida e enriquece produtos via Last.fm API
- [x] Rodar script e gerar `products_enriched.json` com capas, ano, gêneros
- [ ] Revisar manualmente álbuns não encontrados no Last.fm

## 1. Infraestrutura

- [x] Setup do monorepo
- [x] Supabase free tier + schema + RLS + seed
- [x] Variáveis de ambiente configuradas
- [ ] Configurar GitHub Secrets
- [ ] Deploy na Vercel

## 2. Frontend

### Gestão de CDs (Admin) — Implementado

- [x] Busca de álbuns via Last.fm + filtro por artista em chips
- [x] Formulário de adicionar simplificado: só checkboxes, sem URL/query manual
- [x] Hydration fix em `/gerenciar/adicionar`
- [x] Estados de busca: vazio, carregando, erro, sem resultados
- [x] Navegação por teclado (↑↓→ Enter, Esc limpa)
- [x] Auto-foco no input ao entrar
- [x] Hover + highlight no resultado
- [x] Botão "✕" para limpar busca
- [x] Spinner CSS animado no carregamento
- [x] Todas as plataformas marcadas por default ao adicionar CD (não precisa mais selecionar uma a uma)
- [x] Home page com `dynamic = 'force-dynamic'` para evitar cache
- [x] Supabase client com `cache: 'no-store'` no fetch Server Component
- [x] Logging nas API routes de DELETE e POST
- [x] PriceCard: preço vira link clicável para listing_url
- [x] Produto detalhe: link "Ver na loja ↗" abaixo do gráfico
- [x] PriceCard: corrigido hydration error (div + router, stopPropagation no badge)

### Busca de Álbuns — Filtro por Artista

- [x] Input único com ícone 🔍: "Buscar álbum ou artista..."
- [x] Após resultados, chips de artista clicáveis extraídos da resposta
- [x] Clique no chip → filtra resultados client-side (instantâneo)
- [x] Clique de novo → remove filtro
- [x] Contador: "6 resultados encontrados"
- [x] Chips ocultos quando há só 1 artista (não polui)

## 7. Notificações

- [x] `alert.py` + `email_digest.py` implementados
- [ ] Criar conta Resend e configurar domínio

## 8. Devops

- [x] GitHub Actions workflow configurado
- [ ] Adicionar secrets no repositório
- [ ] Testar `workflow_dispatch`

## 3. Scrapers

- [x] Amazon: busca auto-discovery com fallback de seletores + token similarity (✅ FUNCIONANDO)
- [x] Amazon US/UK/DE: marketplace global com `amazon_global.py` (✅ FUNCIONANDO — matching melhorado com penalidade de álbum ausente)
- [x] Americanas, Casas Bahia, Submarino, Carrefour, Extra: adicionados ao schema + dispatch em `main.py` (sem scraper ainda — log "não implementado")
- [x] Mercado Livre: API pública + Playwright fallback (❌ BLOQUEADO)
- [x] Mercado Livre: API oficial com OAuth cliente (🚧 AGUARDANDO APROVACAO ML)
- [x] Shopee: API + Playwright networkidle + __INITIAL_STATE__ (❌ BLOQUEADO)
- [x] Magazine Luiza: Playwright networkidle + akamai detection (❌ BLOQUEADO)
- [x] Enjoei: Playwright com extração direta de `a[href*='/p/']` + fallback de slug + dump HTML debug (✅ CORRIGIDO v0.9.10 — selectores genéricos não funcionavam)
- [x] Scrapers rodam em pipeline semanal com persistência em price_history + scrape_log
- [x] Stealth global: --disable-blink-features, viewport, locale, timezone, geolocation, anti-detect script

## 4. Logs

- [x] API route `GET /api/scrape-logs` (protegida por admin token, service role)
- [x] Página `/gerenciar/logs` com tabela, filtros por status/plataforma
- [x] Link para logs no `/gerenciar`

## 5. Run Scraper (Navbar — Live Logs)

- [x] API `POST /api/scrape/trigger` — local exec + Vercel GHA dispatch
- [x] Filtro `?since=` no `GET /api/scrape-logs` para polling incremental
- [x] `ScrapeButton` — botão "▶ Rodar" no navbar com painel flutuante
- [x] Live log feed com polling a cada 3s, icons por status/plataforma, resumo ao final
- [x] Corrigido: remover auto-timeout de 60s — polling continua até usuário fechar
- [x] Timer de tempo decorrido no botão (⏳ 45s)
- [x] Corrigido: `exec` usa `python -m scraper.main` com cwd na raiz (ModuleNotFoundError)
- [x] Corrigido: mapear `SUPABASE_URL` de `NEXT_PUBLIC_SUPABASE_URL` no exec (KeyError)
- [x] Corrigido: polling não depende mais do painel aberto — polling persiste via sessionStorage entre navegações (corrigido em v0.9.6: estado salvo no sessionStorage para sobreviver a re-mount do componente)
- [x] Auto-stop após 5min sem logs (meio-termo entre timeout curto e infinito)
- [x] Indicador "📡 Xs sem atualização" no painel (fica vermelho após 2min)
- [x] `main.py` — `load_dotenv()` no topo para carregar `scraper/.env` independente do CWD
- [x] Streaming local via SSE substitui polling — `handleClick` lê `ReadableStream` quando `content-type: text/event-stream`; polling vira fallback apenas GHA
- [x] Logs do streaming usam visual unificado de 2 linhas (ℹ️  + info — texto na linha 2), mesmo formato dos logs estruturados — sem branching no render
- [x] Streaming: live status (ℹ️) aparece como entry única no topo, substituída a cada evento; resultados estruturados são buscados ao final e empilhados abaixo
- [x] Live status simplificado: linha única com ℹ️ + texto, sem `🏪` e sem linha "info" redundante
- [x] Polling roda em qualquer modo (local + GHA) para logs estruturados, filtrando apenas entries com `product_platform_config` — resultados aparecem em tempo real durante streaming, não só ao final
- [x] Textos amigáveis: `success` → "encontrado", `not_found` → "não encontrado", `error` → "erro", `skipped_fanmade` → "fanmade ignorado"
- [x] Live status limpa prefixo `timestamp [LEVEL] module:` do log Python — mostra só a mensagem legível
- [x] Linha 2 padronizada: sempre inicia com `STATUS_DISPLAY` (encontrado/erro/não encontrado); success mostra ` → {raw_title}` se for diferente do título do produto; not_found sem detail redundante ("sem resultados")
- [x] Botão de conclusão mostra resumo: `✅ 5 · 2 ⚠️ · 1 ⚪` com fundo verde (ou âmbar se só erros)
- [x] Banner 🎉 no painel ao concluir: "5 encontrados · 2 erros · 1 não encontrado · 35s"
- [x] Corrigido: `<a href="/gerenciar/logs">` → `<Link>` em `gerenciar/page.tsx` (causava perda de estado ao navegar)
- [x] Corrigido: `<a href="/gerenciar">` → `<Link>` em `gerenciar/logs/page.tsx` (Voltar)
- [x] Corrigido: `ERR_INVALID_STATE` no writer SSE — race entre `close` do Python e chunks pendentes; adicionado flag `writerClosed` para impedir writes após fechamento
- [x] Corrigido: `writerClosed = true` antes de `safeSse()` impedia entrega dos eventos `done`/`error` ao cliente — botão nunca via conclusão, safety reset forçava `idle` após 30s
- [x] Simplificado: 5 save effects fundidos em 1 com JSON blob único; `useMemo` nos computados do botão; SSE dispatch extraído para função
- [ ] Adicionar `GITHUB_PAT` no repositório (GitHub Secret)
- [ ] Adicionar `GITHUB_PAT` no `.env.local` da Vercel

## 6. Gestão de Plataformas

- [x] API `PATCH /api/albums/[id]/platforms` — sincroniza plataformas (deleta removidas, insere novas)
- [x] Componente `PlatformManager` — checkboxes com admin auth, integrado no `/produto/[id]`
- [x] `/gerenciar`: labels de plataforma expandidos (BR, US, UK, DE, ML, MGL, AM, CB, SP)

## 9. Expansão

- [ ] Popular CDs via admin panel
- [ ] Monitorar scrape_log para ajustar filtro

---

### Bugs encontrados e corrigidos

- [x] `_search_amazon_with_query()` sem `except` — exceções do Playwright propagavam sem tratamento (corrigido em v0.9.2)
- [x] `POST /api/scrape/trigger` retornava 401 no Windows — `ADMIN_TOKEN` do `.env.local` vinha com `\r` (CRLF) no final, falhando comparação (corrigido em v0.9.4)
- [x] Botão "▶ Rodar" virava ❌ sem feedback — painel não abria no estado `error`; adicionado `"error"` à visibilidade + mensagem no cabeçalho (corrigido em v0.9.3, refinado em v0.9.4)
- [x] `exec` do scraper falhava silenciosamente — se Python não estivesse disponível, o frontend ficava 5min polling sem logs e concluía com 0 resultados (corrigido em v0.9.4: pre-check de `python --version` + fallback escreve erro no Supabase)
- [x] `ADMIN_TOKEN` com `#` era truncado pelo parser de `.env` — token `HonkaiImpact3rd@#` virava `HonkaiImpact3rd@` porque `#` inicia comentário no formato dotenv (corrigido em v0.9.5: removido `#` do token)
- [x] Botão "▶ Rodar" e painel de logs resetavam ao trocar de página — componente desmontava e todo estado React se perdia (corrigido em v0.9.8: state volta a ser inicializado com valores default para SSR match; restore via `useEffect`; **save effects pulam no 1º ciclo** com `isFirstRender` guard, eliminando race condition)
- [x] `ReferenceError: sessionStorage is not defined` — funções inicializadoras de `useState`/`useRef` rodam durante SSR onde `sessionStorage` não existe (corrigido em v0.9.8: state usa valores default no servidor, restore ocorre só no cliente via `useEffect`)
- [x] Scraper Enjoei não extraía produtos — seletores genéricos (`[class*='product-card']`) não casavam com classes hasheadas Vue.js do Enjoei; reescrito para extrair direto de `a[href*='/p/']` + wait_for_selector + dump HTML partial (corrigido em v0.9.10)
- [x] `platformLabels` nos logs só tinha 3 plataformas (amazon, mercado_livre, shopee) — faltavam amazon_us/uk/de, magalu, americanas, casas_bahia, enjoei e as inativas (corrigido em v0.9.10)
- [ ] Scraper Enjoei — URL `/search?q={}` redirecionava para `/@search?q={}&sid=` (busca de loja vs global); corrigido para `/s?q={}` + extração via API GraphQL `graphql-search-x`. **Continua sem achar produtos** — aguardando debug (v0.9.12)
- [x] Botão "▶ Rodar" não iniciava visualmente na 2ª execução — safety reset (`idleSeconds > 30`) detectava `mode="local"` e `lastUpdateAt` do run anterior e abortava; corrigido: `handleClick` agora limpa `mode`, `startedAt`, `lastUpdateAt`, `elapsed`, `idleSeconds` antes de iniciar nova execução (corrigido em v0.9.13)

### Bugs encontrados (pendentes)

- [ ] **Enjoei #191** — URL `/search?q={}` redireciona para `/@search?q={}&sid=` (busca de loja vs global); corrigido para `/s?q={}` + extração via API GraphQL `graphql-search-x`. **Continua sem achar produtos** — aguardando debug (Fase 10 #1)
- [ ] **Resend build error** — `new Resend(process.env.RESEND_API_KEY)` no top-level de `subscribe/route.ts` quebra o `next build` porque a env var não está disponível durante build. Initialização lazy necessária.

## Fase 11 — Correções de Build

| # | Item | Status |
|---|------|--------|
| 1 | **Resend lazy init** — `subscribe/route.ts`: `getResend()` + `getSupabase()` funções, sem top-level `new Resend()` | ✅ |
| 2 | **Supabase client lazy init** — `createClient` não lança exceção sem env vars, não precisa de lazy init | ✅ |
| 3 | **`confirm/route.ts` e `unsubscribe/route.ts`** — apenas Supabase, sem Resend. Seguros. | ✅ |

## Fase 10 — Correções e Implementações (v0.10.0)

| # | Item | Status |
|---|------|--------|
| 1 | **Corrigir Enjoei** — múltiplas URLs de busca (3 tentativas), `best_match` corrigido (artist vs query), extração refatorada em `_try_search_url` | ✅ |
| 2 | **Aplicar RLS no Supabase** — executar `supabase/rls.sql` no SQL Editor | ✅ |
| 3 | **Reuso de Chromium** — contexto único compartilhado entre todas as plataformas (antes: 5+ browsers separados) | ✅ |
| 4 | **Mercado Livre via Firefox** — fallback Firefox adicionado em `scrape_mercadolivre()` quando Chromien detecta CAPTCHA | ✅ |
| 5 | **TOCTOU — Sync de plataformas** — função `sync_product_platforms()` + RPC no lugar do diff manual (transação atômica) | ✅ |
| 6 | **Exibir moeda correta no PriceCard** — `price-card.tsx` agora respeita currency (R$, $, £, €) | ✅ |
| 7 | **Índice `confirmation_token`** — incorporado em `schema.sql` | ✅ |
| 8 | **Lojas não implementadas** — americanas, casas_bahia, submarino, carrefour, extra: remover do CHECK constraint ou implementar | ⏳ |

## Fase 15 — Curadoria de 7 Lojas (v0.13.0) + Hotfix (v0.13.1)

| # | Item | Status |
|---|------|--------|
| 1 | **Base Nuvemshop** — `nuvemshop.py` reutilizável + 4 lojas (Fonoteca, Supernova, Discol, Music House) | ✅ |
| 2 | **Migranet** — `migranet.py` (httpx, Loja Integrada) | ✅ |
| 3 | **Universal Music Store** — `umusicstore.py` (httpx, Vtex API) | ✅ |
| 4 | **A Loja de Discos** — `loja_discos.py` (httpx, custom + categoria) | ✅ |
| 5 | **main.py** — imports + dispatch para as 7 novas | ✅ |
| 6 | **platforms.ts** — 7 badges (FN/SN/DC/MH/MG/UM/LD) + icons | ✅ |
| 7 | **schema.sql** — CHECK constraint + migration executada | ✅ |
| 8 | **CHANGELOG.md + README.md** — docs atualizadas | ✅ |
| 9 | Build (0 erros) | ✅ |
| 10 | 🔴 **Hotfix matching** — `best_match` no lugar de `choose_lowest_price`, detecção de fallback Nuvemshop, `auto_search_query` sem "cd original" | ✅ |

## Fase 14 — UI/UX Login (v0.12.1)

| # | Item | Status |
|---|------|--------|
| 1 | **admin-auth.tsx** — ícone olho para exibir/ocultar senha | ✅ |
| 2 | Verificar build | ✅ (0 erros) |

## Fase 13 — Padronização de Modais (v0.12.0)

| # | Item | Status |
|---|------|--------|
| 1 | **ConfirmModal** — componente reutilizável de confirmação (overlay escuro, título, mensagem, ações) | ✅ |
| 2 | **Toast** — componente de notificação (success/error/info, auto-dismiss 4s, canto inferior direito) | ✅ |
| 3 | **gerenciar/page.tsx** — substituir `confirm()`/`alert()` por ConfirmModal + Toast, adicionar feedback de sucesso | ✅ |
| 4 | **gerenciar/page.tsx** — botão "Sair" que limpa `sessionStorage` e desloga | ✅ |
| 5 | Verificar build | ⏳ |

## Fase 12 — Novos Scrapers (v0.11.0)

| # | Item | Status |
|---|------|--------|
| 1 | **Locomotiva Discos** — `scraper/locomotiva.py` (httpx, Iluria HTML limpo) | ✅ (testado — 3 resultados para "pink floyd the wall") |
| 2 | **Kiwi Discos** — `scraper/kiwi.py` (Playwright, Nuvemshop) | ✅ |
| 3 | **Regards** — `scraper/regards.py` (Playwright, WooCommerce) | ✅ |
| 4 | **CD Point** — `scraper/cdpoint.py` (Playwright, ASP.NET WebForms) | ✅ |
| 5 | Registrar plataformas no frontend (`platforms.ts`) + badges | ✅ |
| 6 | Atualizar CHECK constraint no schema.sql | ✅ |
| 7 | Integrar dispatch em `main.py` | ✅ |
| 8 | Testar scrapers (unitários) + build | ✅ (51/51 testes, build 0 erros) |
| 9 | Executar migration no Supabase | ✅ |
| 10 | Testar Kiwi/Regards/CD Point com Playwright | ❌ Pendente (exige browser) |
| 11 | **AdminAuth com validação** — `admin-auth.tsx` testa token contra servidor antes de aceitar | ✅ |

### Melhorias de segurança e qualidade (v0.9.14)

| # | Item | Status |
|---|------|--------|
| 1 | `scraper/.env` renomeado para `.env.local` + `.gitignore` cobre ambos | ✅ |
| 2 | `ADMIN_TOKEN` removido de logs de erro (`console.error` → `console.warn` sem valores) | ✅ |
| 3 | `AbortController` adicionado ao SSE reader + cleanup no unmount | ✅ |
| 4 | `parse_br_price(None)` → retorna `0.0` em vez de crash | ✅ |
| 5 | TOCTOU race condition no sync de plataformas | ⏳ Pendente (requer SQL) |
| 6 | Erro flood removido: `trigger/route.ts` não insere logs para todas configs ao falhar | ✅ |
| 7 | Índice em `confirmation_token` | ⏳ Pendente (requer SQL) |
| 8 | `scraper/.env` → `.env.local` + `scraper/.env` adicionado ao `.gitignore` | ✅ |
| 9 | `os.environ["KEY"]` → `os.environ.get("KEY", "")` em `supabase_client.py`, `alert.py`, `email_digest.py` | ✅ |
| 10 | Chromium reiniciado por plataforma | 🔄 Não resolvido (performance) |
| 11 | Debug endpoint `GET /api/scrape/trigger` removido | ✅ |
| 12 | Rate limiting no subscribe (1 minuto entre tentativas) | ✅ |
| 13 | `_normalize`, `_token_similarity`, `_first_selector`, `_best_match` extraídos para `scraper/utils.py` | ✅ |
| 14 | Lista de plataformas centralizada em `frontend/lib/platforms.ts` (elimina duplicação em 5 componentes) | ✅ |
| 15 | RLS pendente nas 3 tabelas | ⏳ Pendente (requer SQL) |
| 16 | Subprocess Python recebe apenas env vars necessárias (não `...process.env`) | ❌ Revertido — whitelist quebrou `dotenv` e outros módulos Python; restaurado `...process.env` com override apenas de `SUPABASE_URL` |
| 17 | Erro do Supabase tratado em `gerenciar/page.tsx` e `produto/[id]/page.tsx` | ✅ |
| 18 | `offset` com limite máximo de 10000 em `scrape-logs/route.ts` | ✅ |
| 19 | `params.id` validado em `albums/add/route.ts` | ✅ |
| 20 | `ErrorBoundary` component criado | ✅ |
| 21 | `PlatformManager`: `initialPlatforms` não reseta seleção do usuário em re-renders | ✅ |
| 22 | Array index como key substituído em `price-card.tsx` | ✅ |
| 23 | Testes refatorados para `scraper.utils` + teste `parse_br_price(None)` + novo `test_utils.py` | ✅ |
