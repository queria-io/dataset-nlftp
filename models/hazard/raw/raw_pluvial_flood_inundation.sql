{{ config(materialized='table', tags=['pluvial_flood']) }}

SELECT * FROM read_parquet('data/pluvial_flood/parquet/*.parquet', union_by_name=true)
