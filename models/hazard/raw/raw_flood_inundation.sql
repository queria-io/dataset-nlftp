{{ config(materialized='table', tags=['flood']) }}

SELECT * FROM read_parquet('data/flood/parquet/*.parquet', union_by_name=true)
