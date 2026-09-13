{{ config(materialized='table', tags=['steep_slope']) }}

SELECT * FROM read_parquet('data/steep_slope/parquet/*.parquet', union_by_name=true)
