-- ============================================================
-- Schema do CD Price Tracker
-- Executar no SQL Editor do Supabase Dashboard
-- ============================================================

-- Extensões
create extension if not exists "pgcrypto";

-- ----------------------------------------
-- Tabela: products
-- ----------------------------------------
create table products (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  artist text not null,
  cover_url text,
  lastfm_url text,
  release_date text,
  genre text[] default '{}',
  lastfm_listeners integer,
  created_at timestamptz default now()
);

-- ----------------------------------------
-- Tabela: product_platform_config
-- ----------------------------------------
create table product_platform_config (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id) on delete cascade,
  platform text not null check (platform in ('amazon', 'amazon_us', 'amazon_uk', 'amazon_de', 'mercado_livre', 'shopee', 'magalu', 'enjoei', 'americanas', 'casas_bahia', 'submarino', 'carrefour', 'extra', 'locomotiva', 'kiwi', 'regards', 'cdpoint', 'fonoteca', 'supernova', 'discol', 'music_house', 'migranet', 'umusicstore', 'loja_discos')),
  amazon_url text,
  search_query text,
  active boolean default true,
  created_at timestamptz default now()
);

-- UNIQUE (product_id, platform) previne duplicatas por TOCTOU
-- Se já existirem duplicatas, rodar antes:
--   delete from product_platform_config a
--   using product_platform_config b
--   where a.id < b.id and a.product_id = b.product_id and a.platform = b.platform;
alter table product_platform_config
add constraint product_platform_unique unique (product_id, platform);

-- ----------------------------------------
-- Tabela: price_history
-- ----------------------------------------
create table price_history (
  id uuid primary key default gen_random_uuid(),
  product_platform_config_id uuid references product_platform_config(id) on delete cascade,
  price numeric(10,2) not null,
  currency text default 'BRL',
  availability text check (availability in ('in_stock', 'out_of_stock', 'unknown')),
  seller_name text,
  listing_url text not null,
  scraped_at timestamptz default now()
);

-- ----------------------------------------
-- Tabela: scrape_log
-- ----------------------------------------
create table scrape_log (
  id uuid primary key default gen_random_uuid(),
  product_platform_config_id uuid references product_platform_config(id) on delete set null,
  status text not null check (status in ('success', 'skipped_fanmade', 'error', 'not_found')),
  raw_title text,
  detail text,
  scraped_at timestamptz default now()
);

-- ----------------------------------------
-- Tabela: subscribers
-- ----------------------------------------
create table subscribers (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  confirmed boolean default false,
  confirmation_token text not null,
  unsubscribe_token text not null,
  created_at timestamptz default now()
);

-- ----------------------------------------
-- Índices
-- ----------------------------------------
create index idx_price_history_config_scraped on price_history(product_platform_config_id, scraped_at desc);
create index idx_price_history_product on price_history(product_platform_config_id);
create index idx_product_platform_config_product on product_platform_config(product_id);
create index idx_subscribers_confirmed on subscribers(confirmed);
create index idx_subscribers_confirmation on subscribers(confirmation_token);
create index idx_subscribers_unsubscribe on subscribers(unsubscribe_token);
create index idx_scrape_log_status on scrape_log(status);
create index idx_scrape_log_product on scrape_log(product_platform_config_id);

-- ----------------------------------------
-- Função TOCTOU-safe para sync de plataformas
-- ----------------------------------------
create or replace function sync_product_platforms(
    p_product_id uuid,
    p_platforms text[]
) returns void
language plpgsql
security definer
as $$
begin
    delete from product_platform_config
    where product_id = p_product_id
      and platform not in (select unnest(p_platforms));

    insert into product_platform_config (product_id, platform, amazon_url, search_query)
    select p_product_id, unnest(p_platforms), null, null
    on conflict (product_id, platform) do nothing;
end;
$$;
