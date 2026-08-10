{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/school_district/junior_high/*.parquet', union_by_name=true)
