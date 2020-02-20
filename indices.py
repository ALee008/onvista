import requests
import bs4
import urllib.parse
import pandas as pd
import numpy as np

from tools import clock

url_ = "https://www.onvista.de/index/"


class DAX:
    def __init__(self):
        self.url = urllib.parse.urljoin(url_, "einzelwerte/DAX-Index-20735")
        self.soup = None

    def parse_url_for_components(self) -> None:
        request = requests.get(self.url)
        self.soup = bs4.BeautifulSoup(request.content, "html.parser")

        assert self.soup, "self.soup must not be empty or None"

        return None

    def stock(self, stock_href: str) -> object:
        pass

    @property
    def components(self) -> list:
        components = [comp.get("title") for comp in self.soup if comp.get("class") == ['TEXT_DICK']]

        return components


class Stock:
    def __init__(self, stock_href: str):
        """"""
        self.url = urllib.parse.urljoin("https://www.onvista.de/", stock_href)
        # get isin, e.g.: aktien/Deutsche-Post-Aktie-DE0005552004 -> DE0005552004
        self.isin = stock_href.split("-")[0]
        # get full name. e.g.: aktien/Deutsche-Post-Aktie-DE0005552004 -> Deutsche-Post-Aktie-DE0005552004
        self.fullname = stock_href.split("/")[1]
        self.fundamentals = self._fundamental_figures()
        self.technical = self._technical_figures()
        self.corporate = self._corporate_figures()

    @clock()
    def _get_data_frame_from_url(self, url: str) -> list:
        stock_url = urllib.parse.urljoin(url, self.fullname)
        data_frames = pd.read_html(stock_url, decimal=',', thousands='.')

        return data_frames

    def _fundamental_figures(self) -> list:
        url = "https://www.onvista.de/aktien/fundamental/"
        return self._get_data_frame_from_url(url)

    def _technical_figures(self) -> list:
        url = "https://www.onvista.de/aktien/technische-kennzahlen/"
        return self._get_data_frame_from_url(url)

    def _corporate_figures(self) -> list:
        url = "https://www.onvista.de/aktien/unternehmensprofil/"
        return self._get_data_frame_from_url(url)

    def _revenue_figures(self) -> pd.DataFrame:
        # revenue figures are in second DataFrame in fundamentals
        df = self.fundamentals[1]
        # rename first column
        revenue = df.rename(columns={df.columns[0]: "revenue"})
        revenue = revenue.set_index("revenue")

        return revenue

    def _dividend_figures(self) -> pd.DataFrame:
        # dividend figures are in third DataFrame in fundamentals
        df = self.fundamentals[2]
        # rename first column
        dividend = df.rename(columns={df.columns[0]: "dividend"})
        dividend = dividend.set_index("dividend")

        return dividend

    def _market_capitalization_figures(self) -> pd.DataFrame:
        # market capitalization figures are in eighth DataFrame in fundamentals
        df = self.fundamentals[7]
        # rename first column
        market_cap = df.rename(columns={df.columns[0]: "market_cap"})
        market_cap = market_cap.set_index("market_cap")

        return market_cap

    def _performance_figures(self) -> pd.DataFrame:
        # performance figures are in last DataFrame in technicals
        df = self.technical[-1]
        perf = df.rename(columns={df.columns[0]: "time_span"})
        # set time_span as index
        perf = perf.iloc[:, :2].set_index("time_span")
        # cast column Perf. from `object` to `float`.
        perf = perf["Perf."].str.replace("%", "").str.replace(",", ".").astype(np.float64) / 100

        return perf

    @property
    def market_capitalization(self) -> pd.Series:
        df_market_cap = self._market_capitalization_figures().T["Marktkapitalisierung in Mio. EUR"].astype(np.float64)

        return df_market_cap

    @property
    def dividend_yield(self) -> pd.Series:
        df_dividend = self._dividend_figures().T["Dividendenrendite"]

        return df_dividend

    @property
    def pe_ratio(self) -> pd.Series:
        """Price-To-Earnings-Ratio (P/E Ratio)"""
        df_pe_ratio = self._revenue_figures().T["KGV"]

        return df_pe_ratio

    @property
    def perf_1y(self):
        return self._performance_figures().loc["1 Jahr"]

    @property
    def perf_5y(self):
        return self._performance_figures().loc["5 Jahre"]


if __name__ == '__main__':
    pass
