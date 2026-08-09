{{ config(materialized='table') }}

SELECT * FROM ST_Read('data/transit/N07-22.geojson')
