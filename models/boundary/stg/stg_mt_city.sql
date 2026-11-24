{{ config(materialized='ephemeral') }}

-- ABR の市区町村マスタを mart から読むための stg。列は raw のまま
SELECT * FROM {{ ref('raw_mt_city') }}
