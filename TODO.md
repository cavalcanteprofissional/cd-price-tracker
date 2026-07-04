# TODO — CD Price Tracker

## 1. Infraestrutura

- [x] Setup do monorepo (diretórios, `.gitignore`, `requirements.txt`, `.env.example`, `.python-version`)
- [ ] Criar projeto Supabase (free tier)
- [ ] Rodar schema SQL + RLS policies no Supabase
- [ ] Configurar variáveis de ambiente reais no GitHub Secrets
- [ ] Deploy do frontend na Vercel

## 2. Banco de Dados

- [ ] Seed manual de 5–10 CDs de teste via SQL ou `seed/products.json`
- [ ] Verificar índices e RLS policies

## 3. Scrapers

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

## 4. Notificações

- [x] `alert.py` — alerta de falha do pipeline via Resend
- [x] `email_digest.py` — template HTML + envio do digest semanal
- [ ] Criar conta Resend e configurar domínio
- [ ] Testar envio de email de confirmação
- [ ] Testar envio do digest completo

## 5. Frontend

- [x] Página `/` — listagem de CDs com preços
- [x] Página `/produto/[id]` — histórico + gráfico recharts
- [x] Página `/cadastro` — formulário de email
- [x] API `/api/subscribe` — cadastro + double opt-in
- [x] API `/api/confirm` — confirmação de email
- [x] API `/api/unsubscribe` — cancelamento
- [ ] Validar build em produção na Vercel

## 6. Devops

- [x] GitHub Actions workflow (cron semanal + testes + scrape)
- [ ] Adicionar secrets no repositório GitHub
- [ ] Testar `workflow_dispatch` manual no GitHub
- [ ] Verificar logs da primeira execução

## 7. Expansão

- [ ] Popular ~50 CDs definitivos via seed script
- [ ] Monitorar scrape_log para ajustar filtro anti-fanmade
- [ ] Considerar ThreadPoolExecutor se o scraping ficar lento
