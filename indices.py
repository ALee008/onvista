import requests
import bs4
import urllib.parse
import pandas as pd
import numpy as np


class FinancialIndex:
    url = "https://www.onvista.de/index/"


class DAX(FinancialIndex):
    def __init__(self):
        self.url = urllib.parse.urljoin(FinancialIndex.url, "einzelwerte/DAX-Index-20735")
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
        self.fundamentals = self.fundamental_figures()
        self.technical = self.technical_figures()

    def fundamental_figures(self) -> list:
        url = "https://www.onvista.de/aktien/fundamental/"
        stock_url = urllib.parse.urljoin(url, self.fullname)
        data_frames = pd.read_html(stock_url, decimal=',', thousands='.')

        return data_frames

    def technical_figures(self) -> list:
        url = "https://www.onvista.de/aktien/technische-kennzahlen/"
        stock_url = urllib.parse.urljoin(url, self.fullname)
        data_frames = pd.read_html(stock_url, decimal=',', thousands='.')

        return data_frames

    def revenue_figures(self) -> pd.DataFrame:
        # revenue figures is second DataFrame in fundamentals
        df = self.fundamentals[1]
        # rename first column
        revenue = df.rename(columns={df.columns[0]: "revenue"})
        revenue = revenue.set_index("revenue")

        return revenue

    def dividend_figures(self) -> pd.DataFrame:
        # dividend figures is third DataFrame in fundamentals
        df = self.fundamentals[2]
        # rename first column
        dividend = df.rename(columns={df.columns[0]: "dividend"})
        dividend = dividend.set_index("dividend")

        return dividend

    def market_capitalization_figures(self) -> pd.DataFrame:
        # market capitalization figures is eighth DataFrame in fundamentals
        df = self.fundamentals[7]
        # rename first column
        market_cap = df.rename(columns={df.columns[0]: "market_cap"})
        market_cap = market_cap.set_index("market_cap")

        return market_cap

    @property
    def market_capitalization(self) -> pd.Series:
        df_market_cap = self.market_capitalization_figures().T["Marktkapitalisierung in Mio. EUR"].astype(np.float64)

        return df_market_cap

    @property
    def dividend_yield(self) -> pd.Series:
        df_dividend = self.dividend_figures().T["Dividendenrendite"]

        return df_dividend

    @property
    def pe_ratio(self) -> pd.Series:
        """Price-To-Earnings-Ratio (P/E Ratio)"""
        df_pe_ratio = self.revenue_figures().T["KGV"]

        return df_pe_ratio


if __name__ == '__main__':
    pass
