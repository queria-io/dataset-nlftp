SELECT
    P14_001 AS prefecture,
    P14_002 AS city,
    P14_003 AS admin_code,
    P14_004 AS address,
    P14_005 AS major_class_code,
    {{ welfare_major_class_name('P14_005') }} AS major_class,
    P14_006 AS middle_class_code,
    {{ welfare_middle_class_name('P14_006') }} AS middle_class,
    P14_007 AS minor_class_code,
    {{ welfare_minor_class_name('P14_007') }} AS minor_class,
    P14_008 AS institution_name,
    P14_009 AS administrator_code,
    {{ welfare_administrator_name('P14_009') }} AS administrator,
    P14_010 AS position_accuracy_code,
    {{ welfare_position_accuracy_name('P14_010') }} AS position_accuracy,
    ST_MakeValid(geom) AS geometry
FROM {{ ref('raw_welfare') }}
WHERE geom IS NOT NULL
