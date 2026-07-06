# TODO — CD Price Tracker

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
- [x] Mercado Livre: API + Playwright fallback (❌ BLOQUEADO - CAPTCHA anti-bot)
- [x] Shopee: API + Playwright networkidle + __INITIAL_STATE__ (❌ BLOQUEADO - verify/traffic)
- [x] Magazine Luiza: Playwright networkidle + akamai detection (❌ BLOQUEADO - Akamai 403)
- [x] Scrapers rodam em pipeline semanal com persistência em price_history + scrape_log
- [x] Stealth global: --disable-blink-features, viewport, locale, timezone, geolocation, anti-detect script

### 🎯 Plano: Desbloquear ML e Shopee (futuro)

Estratégias a serem testadas quando houver infraestrutura adequada:

| Abordagem | Complexidade | Custo |
|---|---|---|
| Headful mode (browser visível) em VPS | Média | R$ 30-50/mês VPS |
| Pool de proxies residenciais (BrightData, etc.) | Alta | $10-50/mês |
| API oficial do ML via app registrado (OAuth) | Baixa | Grátis (rate limitado) |
| API oficial da Shopee via parceria | Alta | Difícil de obter |
| Google Shopping como fonte agregada | Média | Grátis (rate limitado) |
| Parse de newsletter/email de ofertas | Baixa | Grátis |

**Prioridade:** tentar API oficial do ML primeiro (só registrar um app), depois Google Shopping como fallback universal.

## 4. Logs

- [x] API route `GET /api/scrape-logs` (protegida por admin token, service role)
- [x] Página `/gerenciar/logs` com tabela, filtros por status/plataforma
- [x] Link para logs no `/gerenciar`

## 5. Expansão para Novas Lojas

### 🏪 Novas plataformas para integrar

| Loja | Vende CDs? | Anti-bot | Status |
|---|---|---|---|
| **Magazine Luiza** | ✅ Sim | ❌ Akamai 403 | Bloqueado |
| **Americanas** | ✅ Sim | ❌ Provável Akamai | Não testado |
| **Casas Bahia** | ✅ Sim | ❌ Provável Akamai | Não testado |
| **Submarino** | ✅ Sim | ❌ Provável Akamai | Não testado |
| **Carrefour** | ✅ Sim | ⚠️ Desconhecido | Não testado |
| **Extra** | ✅ Sim | ⚠️ Desconhecido | Não testado |

### 🚀 Sugestões adicionais

| Loja / Fonte | Vende CDs? | Motivo |
|---|---|---|
| **Google Shopping (API)** | ✅ Agregador | Fonte única para várias lojas; API gratuita 100 consultas/dia |
| **Google Shopping (scrape)** | ✅ Agregador | Alternativa sem API key, mas Google tem anti-bot |
| **Buscapé** | ✅ Comparador | Agrega preços de várias lojas |
| **Zoom** | ✅ Comparador | Similar ao Buscapé |
| **API oficial Mercado Livre** | ✅ Sim | Precisa de app registrado (OAuth), pode funcionar |
| **Mercado Livre** | ❌ Bloqueado | Já temos mas CAPTCHA blocking |
| **Shopee** | ❌ Bloqueado | Já temos mas verify/traffic blocking |
| **Magazine Luiza** | ❌ Bloqueado | Akamai 403 |

### 🔬 Descobertas

**22:23** — Magalu testado: bloqueado por Akamai anti-bot (403 Forbidden, mesma página que ML). A maioria das lojas brasileiras grandes usa solutions anti-bot (Akamai, DataDome, reCAPTCHA) que bloqueiam Playwright headless mesmo com stealth.

### 📋 Plano de implementação revisado

Dado que todas as lojas brasileiras têm anti-bot agressivo, a abordagem precisa mudar:

1. **Curto prazo — Amazon apenas**: Amazon funciona, focar em melhorar cobertura (mais produtos)
2. **Médio prazo — Google Shopping (API)**: Configurar Google Cloud Project + Shopping API
3. **Médio prazo — API oficial ML**: Registrar app no Mercado Livre Developers, usar OAuth
4. **Longo prazo — VPS com headful**: Rodar scrapers em VPS brasileira com browser visível para lojas com Akamai
5. **Alternativa — Comparadores**: Integrar Buscapé/Zoom em vez de lojas individuais

## 9. Expansão

- [ ] Popular CDs via admin panel
- [ ] Monitorar scrape_log para ajustar filtro
