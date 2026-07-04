# CD Price Tracker

Acompanhe semanalmente os preços de CDs (Compact Disc) em Amazon, Mercado Livre e Shopee, com histórico de preços, digest por email e dashboard web.

## Como funciona

1. Uma lista curada de CDs é armazenada no Supabase
2. Toda segunda-feira às 09:00 BRT, um script Python roda via GitHub Actions
3. Para cada CD, o script busca o preço nas plataformas cadastradas
4. Um filtro anti-fanmade remove anúncios suspeitos automaticamente
5. Os preços são salvos em um histórico no banco de dados
6. Um email digest é enviado para todos os assinantes confirmados
7. O dashboard web (Next.js) exibe os preços atuais e o histórico em gráficos

## Estrutura do projeto

```
cd-price-tracker/
├── scraper/                    # Scripts Python de scraping
│   ├── main.py                 # Orquestrador principal
│   ├── amazon.py               # Scraper Amazon
│   ├── mercadolivre.py         # Scraper Mercado Livre
│   ├── shopee.py               # Scraper Shopee
│   ├── filter.py               # Filtro anti-fanmade
│   ├── price_parser.py         # Normalização de preços BRL
│   ├── models.py               # Dataclasses
│   ├── supabase_client.py      # Conexão com Supabase
│   ├── alert.py                # Alerta de falha
│   ├── email_digest.py         # Envio do digest semanal
│   └── requirements.txt
├── frontend/                   # Dashboard Next.js
│   ├── app/
│   │   ├── page.tsx            # Lista de CDs
│   │   ├── produto/[id]        # Histórico + gráfico
│   │   ├── cadastro            # Formulário de email
│   │   └── api/                # API routes (subscribe, confirm, unsubscribe)
│   └── components/
├── .github/workflows/          # GitHub Actions (cron semanal)
├── seed/                       # Dados de exemplo
└── tests/                      # Testes unitários
```

## Stack

| Camada | Tecnologia |
|---|---|
| Scraper | Python + Playwright + playwright-stealth |
| Agendamento | GitHub Actions (cron semanal) |
| Banco | Supabase (Postgres, free tier) |
| Email | Resend (free tier: 100 emails/dia) |
| Frontend | Next.js 14 + recharts (Vercel, free tier) |
| Testes | Pytest |

## Pré-requisitos

- Python 3.12+
- Node.js 20+
- Conta gratuita no [Supabase](https://supabase.com)
- Conta gratuita no [Resend](https://resend.com)
- Conta gratuita no [GitHub](https://github.com)
- Conta gratuita na [Vercel](https://vercel.com) (opcional para deploy)

## Configuração rápida

### 1. Banco de dados

Crie um projeto no Supabase e execute o schema SQL disponível em `cd-price-tracker-skill.md` (seção "Schema do banco" + "Row Level Security").

### 2. Variáveis de ambiente

```bash
cp scraper/.env.example scraper/.env
# Preencha SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY, etc.
```

### 3. Instalar dependências

```bash
# Python
pip install -r scraper/requirements.txt
playwright install chromium

# Frontend
cd frontend && npm install
```

### 4. Rodar testes

```bash
pytest tests/ -v
```

### 5. Scraping manual

```bash
python -m scraper.main
```

### 6. Frontend local

```bash
cd frontend && npm run dev
```

## Como contribuir

Veja o arquivo [TODO.md](TODO.md) para as próximas tarefas planejadas. Pull requests são bem-vindos!

## Licença

MIT
