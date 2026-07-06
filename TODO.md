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
- [x] Corrigido: polling não depende mais do painel aberto — persiste entre navegações
- [x] Auto-stop após 5min sem logs (meio-termo entre timeout curto e infinito)
- [x] Indicador "📡 Xs sem atualização" no painel (fica vermelho após 2min)
- [x] `main.py` — `load_dotenv()` no topo para carregar `scraper/.env` independente do CWD
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
