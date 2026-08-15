{{ config(materialized='table', tags=['medical_area']) }}

SELECT * FROM read_parquet('data/medical_area/secondary/*.parquet', union_by_name=true)
