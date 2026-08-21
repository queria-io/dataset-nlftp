{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/did/A16-20.parquet')
