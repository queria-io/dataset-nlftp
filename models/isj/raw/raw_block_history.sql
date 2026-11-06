-- 過去の版は 14 版で 2 億行を超えるので実体化しない。mart で名前と番号ごとにまとめる
{{ config(materialized='ephemeral', tags=['isj']) }}

SELECT * FROM read_parquet('data/isj/block_history/parquet/*.parquet', union_by_name=true)
