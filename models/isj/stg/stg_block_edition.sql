{{ config(materialized='ephemeral', tags=['isj']) }}

-- 街区レベル位置参照情報の今の版を block_history から読むための stg。列は raw のまま
SELECT * FROM {{ ref('raw_block') }}
