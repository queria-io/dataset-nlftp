{{ config(materialized='table', tags=['landslide_prevention']) }}

SELECT * FROM read_parquet('data/landslide_prevention/parquet/*.parquet', union_by_name=true)
