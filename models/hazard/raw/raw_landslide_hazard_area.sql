{{ config(materialized='table', tags=['landslide']) }}

SELECT * FROM read_parquet('data/landslide/parquet/*.parquet', union_by_name=true)
