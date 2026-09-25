{{ config(materialized='table') }}

SELECT * FROM read_parquet('data/specified_rural_area/parquet/*.parquet', union_by_name=true)
