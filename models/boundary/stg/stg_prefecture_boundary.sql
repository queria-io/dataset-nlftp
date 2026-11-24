{{ config(materialized='ephemeral') }}

-- 都道府県の境界を mart から読むための stg。列は raw のまま
SELECT * FROM {{ ref('raw_prefecture_boundary') }}
