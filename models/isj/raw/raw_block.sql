{{ config(materialized='table', tags=['isj']) }}

SELECT * FROM read_parquet('data/isj/block/parquet/*.parquet', union_by_name=true)
