"""パイプライン共通の zip ダウンロード。

国土数値情報の配信は数十 MB の zip を数十回続けて取るので、途中で切れた応答と
配信側の一時的な 5xx が定期的に出る。取得はパイプラインごとに書かれていたが、
中身は同じで、直すたびに 1 本ずつ同じ修正を足すことになっていた。ここに 1 つ
置いて全パイプラインから呼ぶ。
"""

import http.client
import logging
import shutil
import ssl
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

USER_AGENT = "dataset-nlftp"

# 1 ファイルあたりの取得試行回数
DOWNLOAD_ATTEMPTS = 3

# 1 回のソケット読み出しの待ち時間（秒）。urlopen の既定は無期限で、無音のまま
# 止まった接続を待ち続けてしまうため明示する
DOWNLOAD_TIMEOUT = 60

# 配信側の一時的な不調。これ以外の HTTP エラー（404 など）は取り直しても結果が
# 変わらないので、待たずにそのまま上げる
TRANSIENT_HTTP_CODES = {429, 500, 502, 503, 504}


class TruncatedDownload(Exception):
    """応答が Content-Length より短く終わった。"""


def download(url: str, dest: Path) -> None:
    """url を dest に保存する。一時的な失敗は取り直す。

    読み終えた長さを Content-Length と突き合わせるのは、http.client が
    Content-Length を満たさない EOF を接続終了として黙って扱い、短いファイルが
    そのまま残るため。Content-Length が無い応答では検算できないので、そのときは
    長さを見ない。

    取り直しの対象は、接続まわりの失敗と TRANSIENT_HTTP_CODES の HTTP エラー。
    404 や 403 は待たずに上げる。
    """
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with (
                urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp,
                open(dest, "wb") as f,
            ):
                declared = resp.headers.get("Content-Length")
                shutil.copyfileobj(resp, f, 1024 * 1024)
            received = dest.stat().st_size
            if declared is not None and received != int(declared):
                raise TruncatedDownload(
                    f"{received} bytes received, {declared} declared"
                )
            return
        except (
            URLError,
            TimeoutError,
            ConnectionError,
            http.client.HTTPException,
            ssl.SSLError,
            TruncatedDownload,
        ) as e:
            dest.unlink(missing_ok=True)
            # HTTPError は URLError の派生なので上でまとめて捕まる。恒久的な
            # エラーはここで選り分けて、待たずに上げる
            if isinstance(e, HTTPError) and e.code not in TRANSIENT_HTTP_CODES:
                raise
            if attempt == DOWNLOAD_ATTEMPTS:
                raise
            logger.warning(f"  retrying {url} after {type(e).__name__}: {e}")
            time.sleep(2**attempt)
