"""JBISへのアクセス関数群."""

import datetime
import re
from decimal import Decimal
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from . import utility


class Access:
    """JBISへのアクセスクラス."""

    def __init__(self, *, getter=None):
        """コンストラクタ."""
        if getter:
            self._getter = getter
        else:
            self._getter = utility.HttpGetter()

        self.coursename_id = {
            '札幌': 101, '函館': 102, '福島': 103, '新潟': 104, '東京': 105,
            '中山': 106, '中京': 107, '京都': 108, '阪神': 109, '小倉': 110,
            '門別': 236, '盛岡': 210, '水沢': 211, '浦和': 218, '船橋': 219, '大井': 220, '川崎': 221,
            '金沢': 222, '笠松': 223, '名古屋': 224, '園田': 227, '高知': 231, '佐賀': 232
        }

        self.id_coursename = {v: k for (k, v) in self.coursename_id.items()}

        self.tracktypes = {'芝': '芝', 'ダ': 'ダート', '障': '障害'}

    def iter_sire_entries(self, horseid):
        """指定されたIDの種牡馬の産駒の出走予定を返す."""
        response = self._getter.get(
            f'https://www.jbis.or.jp/horse/{horseid}/sire/entry/')
        soup = BeautifulSoup(response.content, "html.parser")
        h2s = soup.find_all('h2')

        for h2_element in h2s:
            for tr_element in h2_element.find_next('tbody').find_all('tr'):
                tds = tr_element.find_all('td')
                racename_element = tds[1].a
                racename = racename_element.text.strip()
                raceurl = racename_element.get('href')
                match = re.fullmatch(
                    r'/race/(\d{4})(\d{2})(\d{2})/\d+/\d+.html', raceurl)
                date = datetime.date(
                    int(match.group(1)), int(match.group(2)), int(match.group(3)))
                entry = utility.HorseEntry(date, tr_element.find('th').string,
                                           int(tds[0].string), racename, tds[7].string)
                yield entry

    def get_horse_info(self, horseid):
        """指定されたIDの馬の情報を返す."""
        response = self._getter.get(
            f'https://www.jbis.or.jp/horse/{horseid}/')
        soup = BeautifulSoup(response.content, "html.parser")
        return utility.HorseInfo(name=soup.h1.text)

    def iter_race_calendar(self, year: int, month: int):
        """
        指定した月のレーシングカレンダーを取得する.

        Parameters
        -----------
        year : int
            取得対象年.
        month : int
            取得対象月.

        Yields
        ------
        RaceCalendar
            レーシングカレンダー情報.

        """
        urlbase = 'https://www.jbis.or.jp/race/calendar/'
        response = self._getter.get(urlbase,
                                    params={'year': year, 'month': f'{month:02}'})
        soup = BeautifulSoup(response.content, 'html.parser')

        for a_element in soup.find_all('a'):
            href = a_element.get('href')

            date, course = self._get_date_course_from_url(href)

            if not date:
                continue

            url = urljoin(urlbase, href)
            yield utility.RaceCalendar(date, course, url)

    def iter_races_by_url(self, url):
        """
        URLで指定した日、開催場のレース一覧を取得する.

        Parameters
        -----------
        url : str
            情報のあるURL、iter_race_calendarでの取得を想定.

        Yields
        ------
        RaceInfo
            レース情報.

        """
        raceinfo = dict()
        raceinfo['date'], raceinfo['course'] = self._get_date_course_from_url(
            url)

        response = self._getter.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        trs = soup.find('tbody').find_all('tr')

        for tr_element in trs:
            th_element = tr_element.th

            if not th_element:
                continue

            raceinfo['raceno'] = int(th_element.string)
            tds = tr_element.find_all('td')
            racename_link = tds[0].a
            if racename_link is None:
                continue

            raceinfo['racename'] = racename_link.string
            raceinfo['url'] = urljoin(url, racename_link.get('href'))
            raceinfo['tracktype'], raceinfo['distance'] = (
                self._get_tracktype_distance(tds[1].string))
            raceinfo['horsenum'] = int(tds[2].string)
            yield utility.RaceInfo(**raceinfo)

    def get_race_result_by_url(self, url):
        """
        URLで指定したレース結果を取得する.

        Parameters
        -----------
        url : str
            情報のあるURL、iter_race_by_urlでの取得を想定.

        Returns
        ------
        (RaceInfo, [HorseResult])
            (レース情報, 馬ごとの結果)

        """
        raceinfo_dic = dict()
        response = self._getter.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        h1_element = soup.find('h1')
        h1_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日（.）\d{1,2}回(.+?)\d{1,2}日'
        match = re.search(h1_pattern, h1_element.text)
        raceinfo_dic['date'] = datetime.date(int(match.group(1)), int(
            match.group(2)), int(match.group(3)))
        raceinfo_dic['course'] = match.group(4)

        h2_element = soup.find('h2')
        h2_pattern = r'(\d{1,2})R (.+)'
        match = re.match(h2_pattern, list(h2_element.strings)[0])
        raceinfo_dic['raceno'] = int(match.group(1))
        raceinfo_dic['racename'] = match.group(2).strip()

        track_element = soup.find('p', class_='doc-race-01').em
        raceinfo_dic['tracktype'], raceinfo_dic['distance'] = (
            self._get_tracktype_distance(track_element.string))

        cond_element = soup.find(
            'ul', class_='list-inline-02').find_all('li')[2]
        raceinfo_dic['condition'] = cond_element.string.split('：')[1].strip()
        raceinfo_dic['url'] = url

        def horseresult(tr_element):
            result_dic = dict()
            td_elements = tr_element.find_all('td')
            result_dic['order'] = _get_horseresult_order(
                tr_element.th.string.strip(), td_elements[6].string)
            result_dic['name'] = td_elements[2].a.text
            result_dic['poplar'] = utility.int_or_none(
                td_elements[10].string)
            result_dic['weight'] = utility.int_or_none(
                list(td_elements[11].strings)[0])
            result_dic['time'] = _get_timedelta(td_elements[5].text)
            result_dic['url'] = urljoin(url, td_elements[2].a.get('href'))
            result_dic['no'] = int(td_elements[1].string)
            return utility.HorseResult(**result_dic)

        horseresults = [
            horseresult(x) for x in soup.find('table', class_='tbl-data-04').tbody.find_all('tr')
        ]

        raceinfo_dic['horsenum'] = sum(
            1 for x in horseresults
            if x.order.isdigit() or x.order == '競走中止')
        raceinfo = utility.RaceInfo(**raceinfo_dic)

        return raceinfo, horseresults

    def get_racelist_by_horseurl(self, url):
        """
        URLで指定した馬のレース一覧を取得する.

        Parameters
        -----------
        url : str
            情報のあるURL、get_race_result_by_urlでの取得を想定.

        Returns
        ------
        [(RaceInfo, HorseResult)]
            レース情報の一覧.

        """
        racelist_url = urljoin(url, 'record/all/')
        response = self._getter.get(racelist_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        horsename = soup.find('h1').text
        tr_elements = soup.find('tbody').find_all('tr')

        def get_race(tr_element):
            r_dic = dict()
            r_dic['date'] = datetime.datetime.strptime(
                tr_element.th.string, '%Y/%m/%d').date()
            td_elements = tr_element.find_all('td')
            r_dic['course'] = td_elements[0].string.strip()

            if td_elements[1].a:
                r_path = td_elements[1].a.get('href')
                match = re.search(
                    r'/race/result/\d{8}/\d{3}/(\d{2})/', r_path)
                r_dic['raceno'] = int(match.group(1))
                r_dic['url'] = urljoin(
                    racelist_url, td_elements[1].a.get('href'))
            else:
                r_dic['raceno'] = None
                r_dic['url'] = None

            r_dic['racename'] = td_elements[1].text.strip()
            r_dic['tracktype'] = self.tracktypes[td_elements[2].string]
            r_dic['distance'] = int(td_elements[3].string)
            r_dic['condition'] = td_elements[4].string.strip()
            r_dic['horsenum'] = int(td_elements[5].string)
            race = utility.RaceInfo(**r_dic)

            h_dic = dict()
            h_dic['order'] = _get_horseresult_order(
                td_elements[8].string, td_elements[11].string)
            h_dic['name'] = horsename
            h_dic['poplar'] = utility.int_or_none(td_elements[7].string)
            h_dic['weight'] = utility.int_or_none(
                list(td_elements[12].strings)[0])
            h_dic['time'] = _get_timedelta(list(td_elements[10].strings)[0])
            h_dic['url'] = url
            h_dic['no'] = int(td_elements[6].string)

            if re.fullmatch(r'\d+.\d', td_elements[13].string):
                h_dic['money'] = int(Decimal(td_elements[13].string) * 10000)
            else:
                h_dic['money'] = None

            result = utility.HorseResult(**h_dic)
            return race, result

        racelist = [get_race(x) for x in tr_elements]
        racelist.sort(key=lambda x: x[0].date)
        return racelist

    def _get_date_course_from_url(self, url):
        parsed = urlparse(url)
        href = parsed.path
        match = re.fullmatch(
            r'/race/calendar/(\d{4})(\d{2})(\d{2})/(\d{3})/', href)
        if not match:
            return None, None

        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        date = datetime.date(year, month, day)
        course = self.id_coursename[int(match.group(4))]

        return date, course

    def _get_tracktype_distance(self, track_string):
        tracktype = self.tracktypes[track_string[0]]
        distance = int(track_string[1:-1])
        return tracktype, distance


def _get_timedelta(time: str) -> datetime.timedelta:
    match = re.search(r'(?:(\d):)?(\d{2})\.(\d)', time)
    if match:
        if match.group(1):
            minutes = int(match.group(1))
        else:
            minutes = 0

        result = datetime.timedelta(
            minutes=minutes,
            seconds=int(match.group(2)),
            milliseconds=int(match.group(3))*100)
    else:
        result = None

    return result


def _get_horseresult_order(order: str, abend: str):
    if abend == '取消':
        result = '出走取消'
    elif abend == '除外':
        result = '競走除外'
    elif abend == '中止':
        result = '競走中止'
    else:
        result = order

    return result
