{{ config(materialized='table', tags=['storm_surge']) }}

SELECT * FROM read_parquet('data/storm_surge/license.parquet')
