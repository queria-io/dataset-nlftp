{{ config(materialized='table', tags=['storm_surge']) }}

SELECT * FROM read_parquet('data/storm_surge/parquet/*.parquet', union_by_name=true)
