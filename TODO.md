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

- [x] Amazon: busca auto-discovery com fallback de seletores + token similarity
- [x] Mercado Livre: API + Playwright fallback (bloqueado por anti-bot)
- [x] Shopee: API 403 + Playwright fallback (bloqueado por anti-bot)
- [x] Scrapers rodam em pipeline semanal com persistência em price_history + scrape_log

## 4. Logs

- [x] API route `GET /api/scrape-logs` (protegida por admin token, service role)
- [x] Página `/gerenciar/logs` com tabela, filtros por status/plataforma
- [x] Link para logs no `/gerenciar`

## 9. Expansão

- [ ] Popular CDs via admin panel
- [ ] Monitorar scrape_log para ajustar filtro
