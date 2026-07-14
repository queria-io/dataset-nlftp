{{ config(tags=['flood']) }}

-- 洪水浸水想定区域（河川単位・想定最大規模）のポリゴン
SELECT
    region_code,
    river_code,
    river_name,
    admin_name,
    depth_rank,
    {{ flood_depth_label('depth_rank') }} AS depth_label,
    geometry
FROM {{ ref('stg_flood_inundation') }}
