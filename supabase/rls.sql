-- ============================================================
-- Row Level Security — CD Price Tracker
-- Executar APÓS o schema.sql no SQL Editor do Supabase
-- ============================================================

-- ----------------------------------------
-- Tabelas públicas de leitura (anon key pode SELECT)
-- ----------------------------------------
alter table products enable row level security;
alter table product_platform_config enable row level security;
alter table price_history enable row level security;

create policy "Leitura pública de products"
  on products for select using (true);

create policy "Leitura pública de product_platform_config"
  on product_platform_config for select using (true);

create policy "Leitura pública de price_history"
  on price_history for select using (true);

-- ----------------------------------------
-- subscribers: inserção anônima + leitura/atualização via token
-- ----------------------------------------
alter table subscribers enable row level security;

create policy "Inserção anônima em subscribers"
  on subscribers for insert with check (true);

create policy "Leitura própria via confirmation_token"
  on subscribers for select using (confirmation_token = current_setting('request.jwt.claims', true)::json->>'token');

create policy "Leitura própria via unsubscribe_token"
  on subscribers for select using (unsubscribe_token = current_setting('request.jwt.claims', true)::json->>'token');

create policy "Atualização própria via unsubscribe_token"
  on subscribers for update using (unsubscribe_token = current_setting('request.jwt.claims', true)::json->>'token');

-- ----------------------------------------
-- scrape_log: sem acesso público (só service_role)
-- ----------------------------------------
alter table scrape_log enable row level security;

create policy "Acesso service_role ao scrape_log"
  on scrape_log for all using (false);
