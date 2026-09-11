{#
  多段階浸水想定データ（A53）のコードを読める値に直すマクロ。

  浸水深ランクは 3 段階（A53_003）と 6 段階（A53_004）の 2 系統がコードで入る。
  6 段階は 3 段階の 3m 以上をさらに分けたもので、1 と 2 の区切りは両者で同じ。
  6 段階の区切りは洪水浸水想定区域（A31a）の浸水深ランクと同じなので、
  ラベルの表記も flood_depth_label に揃える（ラベルで突き合わせる読み方が
  テーブルをまたいでも成り立つようにする）。

  下限・上限は細かいほうの 6 段階から取り、欠けているときだけ 3 段階で埋める。
  型は hazard スキーマの他のテーブルの depth_min_m / depth_max_m に合わせて DOUBLE。

  地方整備局等コード（配布ファイル名の 2 桁）は原典に対応表が無いので、
  配布ページの区分名をここに持つ。
#}
{% macro multi_stage_flood_depth_rank_3_label(col) %}
  CASE {{ col }}
    WHEN 1 THEN '0.5m未満'
    WHEN 2 THEN '0.5m以上3m未満'
    WHEN 3 THEN '3m以上'
  END
{% endmacro %}

{% macro multi_stage_flood_depth_rank_6_label(col) %}
  CASE {{ col }}
    WHEN 1 THEN '0.5m未満'
    WHEN 2 THEN '0.5m以上3m未満'
    WHEN 3 THEN '3m以上5m未満'
    WHEN 4 THEN '5m以上10m未満'
    WHEN 5 THEN '10m以上20m未満'
    WHEN 6 THEN '20m以上'
  END
{% endmacro %}

{% macro multi_stage_flood_depth_min(rank_6, rank_3) %}
  CAST(
    COALESCE(
      CASE {{ rank_6 }}
        WHEN 1 THEN 0.0
        WHEN 2 THEN 0.5
        WHEN 3 THEN 3.0
        WHEN 4 THEN 5.0
        WHEN 5 THEN 10.0
        WHEN 6 THEN 20.0
      END,
      CASE {{ rank_3 }}
        WHEN 1 THEN 0.0
        WHEN 2 THEN 0.5
        WHEN 3 THEN 3.0
      END
    ) AS DOUBLE
  )
{% endmacro %}

{#
  上限の無い最上位の区分（6 段階の 20m 以上・3 段階の 3m 以上）は NULL。
  6 段階が欠けている行で 3 段階の 3 を上限なしとして扱うと、6 段階が入って
  いれば 5m 未満だったかもしれない行まで上限なしになるが、区分の文字列は
  depth_rank_3_label / depth_rank_6_label に残る。
#}
{% macro multi_stage_flood_depth_max(rank_6, rank_3) %}
  CAST(
    COALESCE(
      CASE {{ rank_6 }}
        WHEN 1 THEN 0.5
        WHEN 2 THEN 3.0
        WHEN 3 THEN 5.0
        WHEN 4 THEN 10.0
        WHEN 5 THEN 20.0
      END,
      CASE WHEN {{ rank_6 }} IS NULL THEN
        CASE {{ rank_3 }}
          WHEN 1 THEN 0.5
          WHEN 2 THEN 3.0
        END
      END
    ) AS DOUBLE
  )
{% endmacro %}

{% macro multi_stage_flood_bureau_name(col) %}
  CASE {{ col }}
    WHEN '81' THEN '北海道開発局'
    WHEN '82' THEN '東北地方整備局'
    WHEN '83' THEN '関東地方整備局'
    WHEN '84' THEN '北陸地方整備局'
    WHEN '85' THEN '中部地方整備局'
    WHEN '86' THEN '近畿地方整備局'
    WHEN '87' THEN '中国地方整備局'
    WHEN '88' THEN '四国地方整備局'
    WHEN '89' THEN '九州地方整備局'
  END
{% endmacro %}
