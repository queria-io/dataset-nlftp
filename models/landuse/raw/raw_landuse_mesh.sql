{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/landuse/parquet/*.parquet')
