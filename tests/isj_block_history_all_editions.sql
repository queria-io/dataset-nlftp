-- 過去の版は都道府県 47 × 版ごとの zip から作る。取り込みが一部落ちても行数が減るだけで
-- ビルドは通ってしまうため、最も古い版（10.0a、2011）から今の版までのすべての年が
-- 最初または最後の版として現れることを検査する。版の数は今の版の年から決めるので、
-- VERSIONS を新しい版にしても書き換えは要らない
WITH years AS (
    SELECT first_edition_year AS y FROM {{ ref('block_history') }}
    UNION
    SELECT last_edition_year FROM {{ ref('block_history') }}
)
SELECT min(y) AS first_year, max(y) AS last_year, count(*) AS edition_count
FROM years
HAVING min(y) <> 2011 OR count(*) <> max(y) - 2011 + 1
