{{ config(materialized='table') }}

SELECT * FROM ST_Read('data/public_facility/P05-22.geojson')
