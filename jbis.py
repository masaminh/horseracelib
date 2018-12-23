"""JBISへのアクセス関数群."""
import datetime
import re

from bs4 import BeautifulSoup

from horseracelib import utility


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
        today = datetime.date.today()

        for h2_element in h2s:
            match = re.fullmatch(
                r"\s?([0-9]{1,2})月\s?([0-9]{1,2})日出走分", h2_element.string)
            month = int(match.group(1))
            day = int(match.group(2))
            date = datetime.date(
                today.year + (0 if today.month <= month else 1), month, day)

            for tr_element in h2_element.find_next('tbody').find_all('tr'):
                tds = tr_element.find_all('td')
                entry = utility.HorseEntry(date, tr_element.find('th').string,
                                           int(tds[0].string), tds[1].text.strip(), tds[7].string)
                yield entry
