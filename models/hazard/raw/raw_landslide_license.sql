{{ config(materialized='table', tags=['landslide']) }}

SELECT * FROM read_parquet('data/landslide/license.parquet')
