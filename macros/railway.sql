{#
  鉄道データ（N02）・駅別乗降客数データ（S12）のコード値を名称に変換するマクロ。

  駅・路線・乗降客数のモデルで同じ区分コードを使うため、CASE 式を共通化する。
    - 鉄道区分コード（N02_001 / S12_004）: RailwayClassCd
    - 事業者種別コード（N02_002 / S12_005）: InstitutionTypeCd
    - 重複コード（S12 の年度ごと）: RailwayDuplicateCd
    - データ有無コード（S12 の年度ごと）: RailwayExistenceCd
#}
{% macro railway_class_name(col) %}
  CASE {{ col }}
    WHEN '11' THEN '普通鉄道JR'
    WHEN '12' THEN '普通鉄道'
    WHEN '13' THEN '鋼索鉄道'
    WHEN '14' THEN '懸垂式鉄道'
    WHEN '15' THEN '跨座式鉄道'
    WHEN '16' THEN '案内軌条式鉄道'
    WHEN '17' THEN '無軌条鉄道'
    WHEN '21' THEN '軌道'
    WHEN '22' THEN '懸垂式モノレール'
    WHEN '23' THEN '跨座式モノレール'
    WHEN '24' THEN '案内軌条式'
    WHEN '25' THEN '浮上式'
  END
{% endmacro %}

{% macro operator_type_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN 'JRの新幹線'
    WHEN '2' THEN 'JR在来線'
    WHEN '3' THEN '公営鉄道'
    WHEN '4' THEN '民営鉄道'
    WHEN '5' THEN '第三セクター'
  END
{% endmacro %}

{% macro railway_duplicate_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN '当該路線駅に記載'
    WHEN '2' THEN '他路線駅に記載'
    WHEN '3' THEN '駅なし'
  END
{% endmacro %}

{% macro railway_data_availability_name(col) %}
  CASE {{ col }}
    WHEN '1' THEN 'データ有'
    WHEN '2' THEN 'データなし'
    WHEN '3' THEN '非公開'
    WHEN '4' THEN '駅なし'
  END
{% endmacro %}
