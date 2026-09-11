{{ config(materialized='table', tags=['multi_stage_flood']) }}

SELECT * FROM read_parquet('data/multi_stage_flood/parquet/*.parquet', union_by_name=true)
