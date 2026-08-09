{{ config(materialized='table') }}

-- 駅×年度の乗降客数。ジオメトリは station と同じく軌道区間ラインの重心を代表点とする。
-- 乗降客数は「当該路線駅に記載」かつ「データ有」のときだけ値が入る。それ以外は
-- 元データでは 0 が入っているが、0 人ではなく「この行には記録が無い」の意味なので
-- NULL にする（他路線の駅に計上されている・非公開・データ無・当時は駅が無い）。
SELECT
    station_code,
    station_group_code,
    station_name,
    operator,
    line_name,
    railway_class_code,
    railway_class,
    operator_type_code,
    operator_type,
    year,
    CASE
        WHEN duplicate_code = '1' AND data_availability_code = '1' THEN passenger_count
    END AS passenger_count,
    data_availability_code,
    data_availability,
    duplicate_code,
    duplicate_status,
    note,
    ST_Centroid(geometry) AS geometry
FROM {{ ref('stg_station_passenger') }}
