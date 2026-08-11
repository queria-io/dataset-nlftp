{{ config(materialized='table', tags=['tsunami']) }}

SELECT * FROM read_parquet('data/tsunami/parquet/*.parquet', union_by_name=true)
