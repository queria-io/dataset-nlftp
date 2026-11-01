{{ config(materialized='table') }}

{{ future_population_mesh_source(
    data_dir='data/future_population_250m',
    prefix='250m_mesh_2024'
) }}
