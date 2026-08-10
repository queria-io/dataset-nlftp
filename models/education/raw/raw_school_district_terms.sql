{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/school_district/terms.parquet')
