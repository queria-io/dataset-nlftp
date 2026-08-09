{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/zoning/parquet/*.parquet', union_by_name=true)
