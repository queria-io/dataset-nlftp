{#
  位置参照情報（街区レベル）の市区町村名を lg_code に引く表を返すマクロ。

  原典に市区町村コードが無いので、ABR の市区町村マスタと都道府県名・市区町村名で
  突き合わせて 6 桁の lg_code を付ける。原典の市区町村名は郡名を含む町村
  （西多摩郡瑞穂町）と含まない町村があり、政令市は市名と区名を続けて書く。
  郡名を落とした名前は同じ道府県の中で重なることがある（北海道の古宇郡泊村と
  国後郡泊村がどちらも「泊村」）。重なる名前で突き合わせると街区の行が増えるので、
  道府県の中で 1 つに決まる名前だけを返す。今の市区町村だけを対象にする。

  返す列: lg_code, pref, name
#}
{% macro isj_city_names() %}
    WITH names AS (
        SELECT lg_code, pref, coalesce(county, '') || city || coalesce(ward, '') AS name
        FROM {{ ref('raw_mt_city') }}
        WHERE ablt_date IS NULL AND city IS NOT NULL
        UNION
        SELECT lg_code, pref, city || coalesce(ward, '') AS name
        FROM {{ ref('raw_mt_city') }}
        WHERE ablt_date IS NULL AND city IS NOT NULL AND county IS NOT NULL
    )
    SELECT lg_code, pref, name
    FROM names
    QUALIFY count(*) OVER (PARTITION BY pref, name) = 1
{% endmacro %}
