"""keiba.go.jpへのアクセス関数群."""
from bs4 import BeautifulSoup

from horseracelib import utility
from horseracelib.utility import HorseResult


class Access:
    """keiba.go.jpへのアクセスクラス."""

    def __init__(self, *, getter=None):
        """コンストラクタ."""
        if getter:
            self._getter = getter
        else:
            self._getter = utility.HttpGetter()

    def get_race_result(self, date, course, raceno):
        """レース結果を取得する."""
        courses = {'門別': 36, '盛岡': 10, '水沢': 11, '浦和': 18, '船橋': 19, '大井': 20, '川崎': 21,
                   '金沢': 22, '笠松': 23, '名古屋': 24, '園田': 27, '高知': 31, '佐賀': 32}

        if course not in courses:
            return None

        params = {'k_raceDate': date.strftime('%Y/%m/%d'),
                  'k_raceNo': raceno, 'k_babaCode': courses[course]}

        response = self._getter.get(
            'http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable', params=params)

        soup = BeautifulSoup(response.content, "html.parser")

        def get_horseresult(tr_element):
            tds = tr_element.find_all('td')
            order = tds[0].string.strip()

            if order == '':
                order = tds[12].string

            poplar = tds[14].string.replace('\xa0', '-')
            return HorseResult(order=order, name=tds[3].text.strip(), poplar=poplar)

        return [get_horseresult(tr)
                for tr in soup.find('tr', class_='dbitem').findNextSiblings('tr')]
