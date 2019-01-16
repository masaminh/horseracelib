"""JBISへのアクセス関数群."""
import datetime
import re

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
