-- 過去の版は都道府県 47 × 版 15 の zip から作る。取り込みが一部落ちても行数が減るだけで
-- ビルドは通ってしまうため、すべての版の年度が最初または最後の版として現れることを検査する
-- （2011〜2025 年の 15 版）
SELECT count(DISTINCT y) AS edition_count
FROM (
    SELECT first_edition_year AS y FROM {{ ref('block_history') }}
    UNION ALL
    SELECT last_edition_year FROM {{ ref('block_history') }}
)
HAVING count(DISTINCT y) <> 15
