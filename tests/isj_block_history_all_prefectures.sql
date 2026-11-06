-- block と同じく、47 都道府県が揃っていることを検査する
SELECT count(DISTINCT prefecture_name) AS prefecture_count
FROM {{ ref('block_history') }}
HAVING count(DISTINCT prefecture_name) <> 47
