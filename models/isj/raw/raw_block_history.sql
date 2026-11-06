-- 過去の版（14 版、2 億行余り）。mart の block_history で名前と番号ごとにまとめる
{{ config(materialized='table', tags=['isj']) }}

SELECT * FROM read_parquet('data/isj/block_history/parquet/*.parquet', union_by_name=true)
