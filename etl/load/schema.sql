create table if not exists raw_listings (
    codigo      text primary key,
    payload     jsonb not null,
    first_seen  timestamptz not null default now(),
    last_seen   timestamptz not null default now(),
    active      boolean not null default true
);

create table if not exists price_history (
    codigo      text not null references raw_listings (codigo),
    observed_at timestamptz not null default now(),
    sale_price  numeric,
    rent_price  numeric,
    primary key (codigo, observed_at)
);

create index if not exists raw_listings_active_idx on raw_listings (active);
