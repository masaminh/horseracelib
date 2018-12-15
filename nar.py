"""keiba.go.jpへのアクセス関数群."""
import datetime
import time

import requests
from bs4 import BeautifulSoup

from horseracelib.utility import HorseResult


class Access:
    """keiba.go.jpへのアクセスクラス."""

    def __init__(self):
        """コンストラクタ."""
        self._lastaccess = datetime.datetime(2000, 1, 1)

    def get_race_result(self, date, course, raceno):
        """レース結果を取得する."""
        courses = {'門別': 36, '盛岡': 10, '水沢': 11, '浦和': 18, '船橋': 19, '大井': 20, '川崎': 21,
                   '金沢': 22, '笠松': 23, '名古屋': 24, '園田': 27, '高知': 31, '佐賀': 32}

        if course not in courses:
            return None

        params = {'k_raceDate': date.strftime('%Y/%m/%d'),
                  'k_raceNo': raceno, 'k_babaCode': courses[course]}

        delta = datetime.datetime.now() - self._lastaccess

        if delta.seconds < 1:
            time.sleep(1 - delta.seconds)

        response = requests.get(
            'http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable', params=params)
        self._lastaccess = datetime.datetime.now()

        soup = BeautifulSoup(response.content, "html.parser")

        def get_horseresult(tr_element):
            tds = tr_element.find_all('td')
            order = tds[0].string.strip()

            if order == '':
                order = tds[12].string

            return HorseResult(order=order, name=tds[3].text.strip(), poplar=tds[14].string)

        return [get_horseresult(tr)
                for tr in soup.find('tr', class_='dbitem').findNextSiblings('tr')]
