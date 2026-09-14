{{ config(materialized='table', tags=['sabo']) }}

SELECT * FROM read_parquet('data/sabo/datapoint.parquet')
