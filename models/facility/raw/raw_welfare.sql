{{ config(materialized='table') }}

SELECT * FROM ST_Read('data/welfare/P14-21.geojson')
