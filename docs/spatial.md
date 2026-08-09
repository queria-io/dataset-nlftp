---
title: 地理データ(GEOMETRY)を扱う
order: 1
---

国土数値情報の境界・施設データは `GEOMETRY` 型の列を持ち、DuckDB の spatial 拡張で扱えます。「この緯度経度はどの市区町村か」という逆ジオコーディングや、境界ポリゴンと施設ポイントの掛け合わせが SQL だけで完結します。

手元の DuckDB で実行する場合は、最初に spatial 拡張をロードしてください(ブラウザ上では自動でロードされます)。

```text
INSTALL spatial;
LOAD spatial;
```

## この緯度経度はどの市区町村か(逆ジオコーディング)

`boundary.municipality` は全国の市区町村境界(政令指定都市は区単位、全1,898件)を持ちます。`ST_Contains` で点を含むポリゴンを探せば、緯度経度から市区町村を特定できます。座標は `ST_Point(経度, 緯度)` の順で指定します。

```sql
SELECT lg_code, prefecture_name, city_name, ward_name
FROM nlftp.boundary.municipality
WHERE ST_Contains(geometry, ST_Point(139.7671, 35.6812))
```

東京駅の座標を渡すと千代田区(`13101`)が返ります。`lg_code` は5桁の市区町村コードなので、そのまま統計データセットとの結合キーになります。

## 境界と施設を掛け合わせる

施設ポイントを市区町村ポリゴンで空間結合すれば、「エリア内に何があるか」を数えられます。千代田区内の学校を数えてみます。

```sql
SELECT COUNT(*) AS schools
FROM nlftp.facility.school s
JOIN nlftp.boundary.municipality m ON ST_Contains(m.geometry, s.geometry)
WHERE m.lg_code = '13101'
```

`facility.school` のように市区町村コード(`admin_code`)を持つテーブルなら普通の JOIN で足りますが、コード列を持たない位置データ(自社の店舗リスト、GPS ログなど)でも、この空間結合パターンならそのまま集計できます。

## GeoJSON で取り出す

`ST_AsGeoJSON` でジオメトリを GeoJSON 文字列に変換できます。ポリゴンの重心なら出力も小さく、地図ライブラリへピンを渡す用途に便利です。

```sql
SELECT
  city_name || coalesce(ward_name, '') AS name,
  ST_AsGeoJSON(ST_Centroid(geometry)) AS center
FROM nlftp.boundary.municipality
WHERE prefecture_code = '13'
LIMIT 5
```

境界ポリゴンをファイルとして書き出したい場合は、手元の DuckDB で GDAL 経由の `COPY` を使います。書き出した GeoJSON は Leaflet や MapLibre、QGIS でそのまま読めます。

```text
COPY (
  SELECT city_name, ward_name, geometry
  FROM nlftp.boundary.municipality
  WHERE prefecture_code = '13'
) TO 'tokyo.geojson' WITH (FORMAT GDAL, DRIVER 'GeoJSON');
```

## 注意点

- 座標は経度・緯度の順です。`ST_Point(緯度, 経度)` と逆に書くと何もヒットしません
- 境界ポリゴンは詳細な形状を持つため、全国を対象にした空間結合は時間がかかります。まず `prefecture_code` や `lg_code` で絞ってから空間条件を使うのが基本です
