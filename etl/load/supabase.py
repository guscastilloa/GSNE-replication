import json

import psycopg

from etl import config


# Queries

ACTIVE_STATUS = "S"

STAGE = """
CREATE TEMP TABLE stage (
n BIGINT,
codigo TEXT,
payload TEXT
) ON COMMIT DROP
"""

UPSERT = """
INSERT INTO raw_listings (codigo, payload, first_seen, last_seen, active)
SELECT DISTINCT ON (codigo)
    codigo,
    payload::jsonb,
    now(),
    now(),
    (payload::jsonb ->> 'publicationStatus') = %(active_status)s
FROM stage
ORDER BY codigo,n DESC
ON CONFLICT (codigo) DO UPDATE
SET payload = excluded.payload,
    last_seen = excluded.last_seen,
    active = excluded.active
"""


PRICES = r"""
WITH staged AS (
    SELECT DISTINCT ON (codigo)
           codigo,
           CASE WHEN payload::jsonb ->> 'salePrice' ~ '^[0-9]+(\.[0-9]+)?$'
                THEN (payload::jsonb ->> 'salePrice')::numeric END AS sale,
           CASE WHEN payload::jsonb ->> 'rentPrice' ~ '^[0-9]+(\.[0-9]+)?$'
                THEN (payload::jsonb ->> 'rentPrice')::numeric END AS rent
    FROM stage
    ORDER BY codigo, n DESC
)
INSERT INTO price_history (codigo, observed_at, sale_price, rent_price)
SELECT s.codigo, now(), s.sale, s.rent
FROM staged s
LEFT JOIN LATERAL (
    SELECT ph.sale_price, ph.rent_price
    FROM price_history ph
    WHERE ph.codigo = s.codigo
    ORDER BY ph.observed_at DESC
    LIMIT 1
) prev ON true
WHERE s.sale IS DISTINCT FROM prev.sale_price
   OR s.rent IS DISTINCT FROM prev.rent_price
"""
 
UNCAST = r"""
SELECT count(*) FROM stage
WHERE (payload::jsonb ->> 'salePrice') IS NOT NULL
  AND (payload::jsonb ->> 'salePrice') !~ '^[0-9]+(\.[0-9]+)?$'
"""


def load(src_path):
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(STAGE)
        staged = _copy(cur, src_path)

        uncast = cur.execute(UNCAST).fetchone()[0]
        if uncast:
            print(f"warning {uncast}  salePrice values did not parse as numeric")

        cur.execute(UPSERT, {"active_status": ACTIVE_STATUS})
        upserted = cur.rowcount

        cur.execute(PRICES)
        priced = cur.rowcount

    print(f"staged {staged} · upserted {upserted} · price rows {priced}")


def ping():
    with psycopg.connect(config.require("SUPABASE_DB_URL")) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from raw_listings")
        print(f"raw_listings: {cur.fetchone()[0]} rows")


def _copy(cur, src_path):
    n = 0
    with cur.copy("COPY stage (n, codigo, payload) FROM STDIN") as cp, open(src_path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            cp.write_row((i, json.loads(line)["propertyId"], line))
            n += 1
    return n

def _connect():
    return psycopg.connect(config.require("SUPABASE_DB_URL"))