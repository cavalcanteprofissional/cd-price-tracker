-- ============================================================
-- Seed data — CD Price Tracker
-- Executar APÓS schema.sql + rls.sql no SQL Editor do Supabase
-- ============================================================

begin;

-- ----------------------------------------
-- Products (5 CDs enriquecidos via Last.fm)
-- ----------------------------------------
insert into products (id, title, artist, cover_url, lastfm_url, release_date, genre, lastfm_listeners) values
  (
    gen_random_uuid(),
    'Thriller',
    'Michael Jackson',
    'https://lastfm.freetls.fastly.net/i/u/300x300/85fdc23b75d77d4cf789fd1904d06863.png',
    'https://www.last.fm/music/Michael+Jackson/Thriller',
    '1982-11-30',
    '{pop,80s,michael jackson,1982,dance}',
    null
  ),
  (
    gen_random_uuid(),
    'Abbey Road',
    'The Beatles',
    'https://lastfm.freetls.fastly.net/i/u/300x300/f304ba0296794c6fc9d0e1cccd194ed0.png',
    'https://www.last.fm/music/The+Beatles/Abbey+Road',
    '1969-09-26',
    '{rock,1969,60s,classic rock,pop}',
    null
  ),
  (
    gen_random_uuid(),
    'The Dark Side of the Moon',
    'Pink Floyd',
    'https://lastfm.freetls.fastly.net/i/u/300x300/d4bdd038cacbec705e269edb0fd38419.png',
    'https://www.last.fm/music/Pink+Floyd/The+Dark+Side+of+the+Moon',
    '1973-03-01',
    '{progressive rock,psychedelic rock,classic rock,rock,pink floyd}',
    null
  ),
  (
    gen_random_uuid(),
    'Nevermind',
    'Nirvana',
    'https://lastfm.freetls.fastly.net/i/u/300x300/e8693de0a153e609b3eaebb42d62e8be.png',
    'https://www.last.fm/music/Nirvana/Nevermind',
    '1991-09-24',
    '{grunge,rock,90s,alternative,alternative rock}',
    null
  ),
  (
    gen_random_uuid(),
    'OK Computer',
    'Radiohead',
    'https://lastfm.freetls.fastly.net/i/u/300x300/62d26c6cb4ac4bdccb8f3a2a0fd55421.png',
    'https://www.last.fm/music/Radiohead/OK+Computer',
    '1997-05-21',
    '{alternative,alternative rock,rock,radiohead,indie}',
    null
  );

-- ----------------------------------------
-- Product Platform Config (URLs e queries de busca)
-- ----------------------------------------
-- Thriller: Amazon + Mercado Livre + Shopee
insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'amazon', 'https://www.amazon.com.br/dp/B001234567', null
from products p where p.title = 'Thriller' and p.artist = 'Michael Jackson';

insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'mercado_livre', null, 'thriller michael jackson cd original'
from products p where p.title = 'Thriller' and p.artist = 'Michael Jackson';

insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'shopee', null, 'thriller michael jackson cd'
from products p where p.title = 'Thriller' and p.artist = 'Michael Jackson';

-- Abbey Road: Amazon + Mercado Livre
insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'amazon', 'https://www.amazon.com.br/dp/B000123456', null
from products p where p.title = 'Abbey Road' and p.artist = 'The Beatles';

insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'mercado_livre', null, 'abbey road beatles cd original'
from products p where p.title = 'Abbey Road' and p.artist = 'The Beatles';

-- The Dark Side of the Moon: Mercado Livre + Shopee
insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'mercado_livre', null, 'dark side of the moon pink floyd cd'
from products p where p.title = 'The Dark Side of the Moon' and p.artist = 'Pink Floyd';

insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'shopee', null, 'dark side of the moon pink floyd cd'
from products p where p.title = 'The Dark Side of the Moon' and p.artist = 'Pink Floyd';

-- Nevermind: Amazon + Mercado Livre
insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'amazon', 'https://www.amazon.com.br/dp/B000987654', null
from products p where p.title = 'Nevermind' and p.artist = 'Nirvana';

insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'mercado_livre', null, 'nevermind nirvana cd original'
from products p where p.title = 'Nevermind' and p.artist = 'Nirvana';

-- OK Computer: Shopee
insert into product_platform_config (product_id, platform, amazon_url, search_query)
select p.id, 'shopee', null, 'ok computer radiohead cd'
from products p where p.title = 'OK Computer' and p.artist = 'Radiohead';

commit;
