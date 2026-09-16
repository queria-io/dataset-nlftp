"""パイプライン共通の HTTP 取得。

国土数値情報の配信は数十 MB の zip を数十回続けて取るので、途中で切れた応答と
配信側の一時的な 5xx が定期的に出る。取得はパイプラインごとに書かれていたが、
中身は同じで、直すたびに 1 本ずつ同じ修正を足すことになっていた。ここに 1 つ
置いて全パイプラインから呼ぶ。

取得の形は 3 つある。zip を保存する `download()`、配布ページの HTML を読む
`fetch_text()`、URL の存在を HEAD で確かめる `url_exists()`。待ち時間の上限と
取り直しの条件は 3 つで同じものを使う。取得元が同じである以上、zip だけが
不安定という理由が無いため。
"""

import http.client
import logging
import shutil
import ssl
import time
from collections.abc import Callable
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


def _retrying[T](
    url: str, attempt: Callable[[], T], cleanup: Callable[[], None] | None = None
) -> T:
    """attempt を呼び、一時的な失敗なら取り直す。

    取り直しの対象は、接続まわりの失敗と TRANSIENT_HTTP_CODES の HTTP エラー。
    404 や 403 は待たずに上げる。cleanup は失敗のたびに呼ぶ（書きかけのファイルを
    消すのに使う）。
    """
    for n in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            return attempt()
        except (
            URLError,
            TimeoutError,
            ConnectionError,
            http.client.HTTPException,
            ssl.SSLError,
            TruncatedDownload,
        ) as e:
            if cleanup is not None:
                cleanup()
            # HTTPError は URLError の派生なので上でまとめて捕まる。恒久的な
            # エラーはここで選り分けて、待たずに上げる
            if isinstance(e, HTTPError) and e.code not in TRANSIENT_HTTP_CODES:
                raise
            if n == DOWNLOAD_ATTEMPTS:
                raise
            logger.warning(f"  retrying {url} after {type(e).__name__}: {e}")
            time.sleep(2**n)
    raise AssertionError("unreachable")


def download(url: str, dest: Path) -> None:
    """url を dest に保存する。一時的な失敗は取り直す。

    読み終えた長さを Content-Length と突き合わせるのは、http.client が
    Content-Length を満たさない EOF を接続終了として黙って扱い、短いファイルが
    そのまま残るため。Content-Length が無い応答では検算できないので、そのときは
    長さを見ない。
    """

    def attempt() -> None:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with (
            urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp,
            open(dest, "wb") as f,
        ):
            declared = resp.headers.get("Content-Length")
            shutil.copyfileobj(resp, f, 1024 * 1024)
        received = dest.stat().st_size
        if declared is not None and received != int(declared):
            raise TruncatedDownload(f"{received} bytes received, {declared} declared")

    _retrying(url, attempt, cleanup=lambda: dest.unlink(missing_ok=True))


def fetch_text(url: str, encoding: str = "utf-8") -> str:
    """url の本文を文字列で返す。一時的な失敗は取り直す。

    配布ページの HTML を読む経路。どのパイプラインでも最初に走るので、ここで
    無音のまま止まると zip を 1 つも取らないままジョブの上限まで動き続ける。
    """

    def attempt() -> str:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
            return resp.read().decode(encoding, errors="replace")

    return _retrying(url, attempt)


def url_exists(url: str) -> bool:
    """HEAD リクエストで url の存在を確認する（404 は False）。

    404 以外の HTTP エラーはそのまま上げる。無い URL と、取りに行けなかった URL を
    同じ「無い」に畳むと、配信側の不調の日に取得対象が黙って減るため。
    """

    def attempt() -> bool:
        req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=DOWNLOAD_TIMEOUT):
            return True

    try:
        return _retrying(url, attempt)
    except HTTPError as e:
        if e.code == 404:
            return False
        raise
