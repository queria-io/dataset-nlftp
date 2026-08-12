{{ config(materialized='table', tags=['tsunami']) }}

SELECT * FROM read_parquet('data/tsunami/license.parquet')
