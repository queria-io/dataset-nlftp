{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/metropolitan_area/parquet/*.parquet', union_by_name=true)
