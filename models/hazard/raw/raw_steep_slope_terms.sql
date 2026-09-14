{{ config(materialized='table', tags=['steep_slope']) }}

SELECT * FROM read_parquet('data/steep_slope/terms.parquet')
