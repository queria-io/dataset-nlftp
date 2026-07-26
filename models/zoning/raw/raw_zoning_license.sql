{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/zoning/license.parquet')
