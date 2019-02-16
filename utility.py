"""競馬関係のユーティリティ."""
import datetime
import time
from typing import NamedTuple
from collections import namedtuple

import requests

HorseInfo = namedtuple('HorseInfo', ['name'])


class HorseResult(NamedTuple):
    """
    馬ごとの結果.

    Attributes
    ----------
    order : str
        順位 (競走中止等を含むため文字列).
    name : str
        馬名.
    poplar : int
        人気.
    weight : int
        馬体重.
    time : datetime.timedelta
        タイム (秒)
    url : str
        馬情報へのURL.
    money : int
        獲得賞金.
    no: int
        馬番.

    """

    order: str
    name: str
    poplar: int
    weight: int = None
    time: datetime.timedelta = None
    url: str = None
    money: int = None
    no: int = None


HorseEntry = namedtuple(
    'HorseEntry', ['date', 'course', 'raceno', 'racename', 'horsename'])


RaceCalendar = namedtuple('RaceCalendar', ['date', 'course', 'url'])


class RaceInfo(NamedTuple):
    """
    レース情報.

    Attributes
    ----------
    date: datetime.date
        開催日.
    course: str
        競馬場.
    raceno: int
        レース番号.
    racename: str
        レース名.
    tracktype: str
        コース(芝/ダート/障害)
    distance: int
        距離.
    condition: str = None
        馬場状態.
    horsenum: int = None
        頭数.
    url: str = None
        URL.

    """

    date: datetime.date
    course: str
    raceno: int
    racename: str
    tracktype: str
    distance: int
    condition: str = None
    horsenum: int = None
    url: str = None


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


def int_or_none(src: str):
    """
    文字列をintで返す。変換不能の場合はNone.

    Parameters
    ----------
    s: str
        変換元の文字列.

    Returns
    -------
    変換結果の数値.変換不能の場合はNone.

    """
    return int(src) if src.isdigit() else None
