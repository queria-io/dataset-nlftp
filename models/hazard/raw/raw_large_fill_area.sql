{{ config(materialized='table', tags=['large_fill']) }}

SELECT * FROM read_parquet('data/large_fill/parquet/*.parquet', union_by_name=true)
