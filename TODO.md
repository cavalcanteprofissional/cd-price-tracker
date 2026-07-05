# TODO — CD Price Tracker

## 0. Validação de Álbuns (Last.fm API)

- [x] Criar conta no Last.fm e gerar API Key
- [x] `seed/validate_albums.py` — valida e enriquece produtos via Last.fm API
- [x] Rodar script e gerar `products_enriched.json` com capas, ano, gêneros
- [ ] Revisar manualmente álbuns não encontrados no Last.fm

## 1. Infraestrutura

- [x] Setup do monorepo (diretórios, `.gitignore`, `requirements.txt`, `.env.example`, `.python-version`)
- [x] Criar projeto Supabase (free tier)
- [x] `supabase/schema.sql` — arquivo SQL com CREATE TABLEs + índices
- [x] `supabase/rls.sql` — arquivo SQL com RLS policies
- [x] `supabase/seed.sql` — arquivo SQL com INSERTs dos produtos enriquecidos
- [x] Schema + RLS + seed aplicados no Supabase via MCP
- [x] Variáveis de ambiente configuradas nos `.env` locais
- [ ] Configurar variáveis de ambiente reais no GitHub Secrets
- [ ] Deploy do frontend na Vercel

## 2. Banco de Dados

- [x] Verificar índices e RLS policies
- [x] Verificar dados do seed no banco (5 CDs com Last.fm metadata)

## 3. Frontend

- [ ] Corrigir `price-card.tsx` — adicionar `"use client"` para aceitar event handlers
- [ ] Rodar `npm run dev` e validar página inicial
- [ ] Rodar `npm run build` para validar build
- [ ] Página `/produto/[id]` — histórico + gráfico recharts
- [ ] Página `/cadastro` — formulário de email
- [ ] API `/api/subscribe` — cadastro + double opt-in
- [ ] API `/api/confirm` — confirmação de email
- [ ] API `/api/unsubscribe` — cancelamento

## 4. Scrapers

- [x] `filter.py` — filtro anti-fanmade (regex)
- [x] `price_parser.py` — normalização de preço BRL
- [x] `models.py` — dataclasses tipadas
- [x] `amazon.py` — scraper Amazon com Playwright + stealth
- [x] `mercadolivre.py` — scraper Mercado Livre (busca + filtro + menor preço)
- [x] `shopee.py` — scraper Shopee via API interna + fallback Playwright
- [x] `main.py` — orquestrador com retry (tenacity), logging, persistência
- [ ] Validar scraper Amazon localmente com URL real
- [ ] Validar scraper Mercado Livre localmente
- [ ] Validar scraper Shopee localmente

## 5. Notificações

- [x] `alert.py` — alerta de falha do pipeline via Resend
- [x] `email_digest.py` — template HTML + envio do digest semanal
- [ ] Criar conta Resend e configurar domínio
- [ ] Testar envio de email de confirmação
- [ ] Testar envio do digest completo

## 6. Devops

- [x] GitHub Actions workflow (cron semanal + testes + scrape)
- [ ] Adicionar secrets no repositório GitHub
- [ ] Testar `workflow_dispatch` manual no GitHub
- [ ] Verificar logs da primeira execução

## 7. Expansão

- [ ] Popular ~50 CDs definitivos via seed script
- [ ] Monitorar scrape_log para ajustar filtro anti-fanmade
- [ ] Considerar ThreadPoolExecutor se o scraping ficar lento
