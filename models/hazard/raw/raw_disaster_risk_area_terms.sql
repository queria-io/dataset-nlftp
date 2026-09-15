{{ config(materialized='table', tags=['disaster_risk_area']) }}

SELECT * FROM read_parquet('data/disaster_risk_area/terms.parquet')
