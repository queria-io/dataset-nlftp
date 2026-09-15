{{ config(materialized='table', tags=['landslide_prevention']) }}

SELECT * FROM read_parquet('data/landslide_prevention/terms.parquet')
