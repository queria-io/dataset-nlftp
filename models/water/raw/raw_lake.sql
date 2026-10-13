{{ config(materialized='table', tags=['lake']) }}

SELECT * FROM read_parquet('data/lake/parquet/*.parquet', union_by_name=true)
