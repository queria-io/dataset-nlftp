{{ config(materialized='table', tags=['lowland']) }}

SELECT * FROM read_parquet('data/lowland/parquet/*.parquet', union_by_name=true)
