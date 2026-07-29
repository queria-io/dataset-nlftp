-- バス停留所のステージング。
--
-- 原典は 1 つのバス停に紐づく系統を P11_003_01〜35 / P11_004_01〜35 の 35 組に
-- 分けて持つ。1 組の中でも系統はカンマ区切りで詰め込まれている（24 件で次の組に
-- 送られる）ため、35 組を順に連結してからカンマで分解する。系統名と区分コードは
-- 同じ位置で対応する。
WITH combined AS (
    SELECT
        prefecture_code,
        P11_001 AS stop_name,
        P11_002 AS operator,
        concat_ws(
            ','
            {%- for slot in range(1, 36) -%}
            , NULLIF(P11_003_{{ '%02d' | format(slot) }}, '')
            {%- endfor %}
        ) AS route_names,
        concat_ws(
            ','
            {%- for slot in range(1, 36) -%}
            , NULLIF(P11_004_{{ '%02d' | format(slot) }}, '')
            {%- endfor %}
        ) AS bus_class_codes,
        P11_005 AS remarks,
        ST_MakeValid(geom) AS geometry
    FROM {{ ref('raw_bus_stop') }}
    WHERE geom IS NOT NULL
),

parsed AS (
    SELECT
        *,
        list_filter(str_split(route_names, ','), name -> name <> '') AS route_list,
        list_sort(list_distinct(
            list_filter(str_split(bus_class_codes, ','), code -> code <> '')
        )) AS class_list
    FROM combined
)

SELECT
    prefecture_code,
    stop_name,
    operator,
    NULLIF(array_to_string(class_list, ','), '') AS bus_class_codes,
    NULLIF(
        array_to_string(
            list_transform(class_list, code -> {{ bus_class_name('code') }}), '／'
        ),
        ''
    ) AS bus_classes,
    len(route_list) AS route_count,
    NULLIF(array_to_string(route_list, ','), '') AS routes,
    remarks,
    geometry
FROM parsed
