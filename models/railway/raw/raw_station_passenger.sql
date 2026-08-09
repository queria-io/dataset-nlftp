{{ config(materialized='table') }}

SELECT * FROM ST_Read('data/station_passenger/S12-25_NumberOfPassengers.shp')
