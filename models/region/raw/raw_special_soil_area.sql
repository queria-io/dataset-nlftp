{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/special_soil_area/parquet/*.parquet', union_by_name=true)
