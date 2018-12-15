"""netkeiba.comへのアクセス関数群."""
import datetime
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from horseracelib.utility import HorseResult


class Access:
    """netkeiba.comへのアクセスクラス."""

    def __init__(self):
        """コンストラクタ."""
        self._lastaccess = datetime.datetime(2000, 1, 1)

    def get_race_result(self, date, course, raceno):
        """レース結果を取得する (本日分のみ)."""
        url = self._get_raceurl(
            'https://race.netkeiba.com/', date, course, raceno)
        response = self._requests_get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        trs = soup.find('table', summary='レース結果').find_all('tr')

        def get_horseresult(tr_element):
            tds = tr_element.find_all('td')
            return HorseResult(tds[0].string, tds[3].a.string, tds[9].string)

        return [get_horseresult(tr) for (i, tr) in enumerate(trs) if i > 0]

    def _get_raceurl(self, urlbase, date, course, raceno):
        courses = {'札幌': 1, '函館': 2, '福島': 3, '新潟': 4, '東京': 5,
                   '中山': 6, '中京': 7, '京都': 8, '阪神': 9, '小倉': 10}

        if course not in courses:
            return None

        params = {'pid': 'race_list_sub', 'id': f'c{date.strftime("%m%d")}'}

        response = self._requests_get(urlbase, params=params)

        soup = BeautifulSoup(response.content, 'html.parser')

        url = None
        hrefs = (x.find('a').get('href')
                 for x in soup.find_all('div', class_='racename'))
        reg = re.compile(
            f'id=.{date.year:04}{courses[course]:02}....{raceno:02}')
        for href in hrefs:
            if reg.search(href):
                url = urljoin(urlbase, href)
                break

        if url is None:
            return None

        return url

    def _requests_get(self, url, params=None):
        delta = datetime.datetime.now() - self._lastaccess

        if delta.seconds < 1:
            time.sleep(1 - delta.seconds)

        response = requests.get(url, params=params)
        self._lastaccess = datetime.datetime.now()
        return response
