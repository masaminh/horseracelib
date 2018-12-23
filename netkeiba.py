"""netkeiba.comへのアクセス関数群."""
import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from horseracelib import utility
from horseracelib.utility import HorseResult


class Access:
    """netkeiba.comへのアクセスクラス."""

    def __init__(self, *, getter=None):
        """コンストラクタ."""
        if getter:
            self._getter = getter
        else:
            self._getter = utility.HttpGetter()

    def get_race_result(self, date, course, raceno):
        """レース結果を取得する (本日分のみ)."""
        url = self._get_raceurl(
            'https://race.netkeiba.com/', date, course, raceno)

        if url is None:
            return None

        response = self._getter.get(url)
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

        response = self._getter.get(urlbase, params=params)

        soup = BeautifulSoup(response.content, 'html.parser')

        url = None
        hrefs = (x.find('a').get('href')
                 for x in soup.find_all('div', class_='racename'))
        reg = re.compile(
            f'.{date.year:04}{courses[course]:02}....{raceno:02}')
        for href in hrefs:
            query_params = parse_qs(urlparse(href).query)

            if query_params['pid'][0] == 'race' and reg.search(query_params['id'][0]):
                url = urljoin(urlbase, href)
                break

        return url
