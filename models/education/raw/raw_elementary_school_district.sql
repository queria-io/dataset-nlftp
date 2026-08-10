{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/school_district/elementary/*.parquet', union_by_name=true)
