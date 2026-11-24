{{ config(materialized='ephemeral', tags=['sabo']) }}

-- 砂防指定地のデータ時点を mart から読むための stg。列は raw のまま
SELECT * FROM {{ ref('raw_sabo_datapoint') }}
