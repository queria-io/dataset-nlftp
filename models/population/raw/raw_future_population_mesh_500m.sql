{{ config(materialized='table') }}

{{ future_population_mesh_source(
    data_dir='data/future_population_500m',
    prefix='500m_mesh_2024'
) }}
