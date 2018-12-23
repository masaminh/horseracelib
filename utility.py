"""競馬関係のユーティリティ."""
import datetime
import time
from collections import namedtuple

import requests

HorseResult = namedtuple('HorseResult', ['order', 'name', 'poplar'])
HorseEntry = namedtuple(
    'HorseEntry', ['date', 'course', 'raceno', 'racename', 'horsename'])

GetterResponseType = namedtuple('ResponseType', ['content'])


class HttpGetter:
    """HTTPを使った取得クラス."""

    def __init__(self):
        """コンストラクタ."""
        self._lastaccess = datetime.datetime(2000, 1, 1)

    def get(self, url, params=None):
        """一秒以上の間隔を開けてurlから情報を取得する."""
        delta = datetime.datetime.now() - self._lastaccess

        if delta.seconds < 1:
            time.sleep(1 - delta.seconds)

        response = requests.get(url, params=params)
        self._lastaccess = datetime.datetime.now()

        return GetterResponseType(content=response.content)
