{{ config(materialized='table', tags=['sabo']) }}

SELECT * FROM read_parquet('data/sabo/parquet/*.parquet', union_by_name=true)
