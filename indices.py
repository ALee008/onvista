import requests
import bs4
import urllib.parse
import pandas as pd
import numpy as np

from tools import logger


url_ = "https://www.onvista.de/index/einzelwerte/"


class Index:
    def __init__(self, index_url: str):
        self.url = urllib.parse.urljoin(url_, index_url)
        self._soup = self.parse_url_for_components()
        self._stock_to_href_dict = self._create_stock_to_href_dict()
        self.prepared_components = None

    def parse_url_for_components(self) -> bs4.BeautifulSoup:
        request = requests.get(self.url)
        soup = bs4.BeautifulSoup(request.content, "html.parser")

        assert soup, "self.soup must not be empty or None"

        return soup

    def _create_stock_to_href_dict(self) -> dict:
        """get all components from DAX components table. For instance:

        >>> print(_components_details[0])
        <a class="TEXT_DICK" href="/aktien/Deutsche-Bank-Aktie-DE0005140008" title="DEUTSCHE BANK AG">Deutsche Bank</a>
        :return (dict): maps company name -> href to stock info
        """
        _components_details = self._soup.find_all("a", attrs={"class": ["TEXT_DICK"]})

        # get components name in upper case
        components = [comp.string.replace(" ", "-") if '...' not in comp.string else comp.get("title")
                      for comp in _components_details]
        components = list(map(str.upper, components))
        hrefs = [comp.get("href") for comp in _components_details]

        assert len(components) == len(hrefs), "number of stocks and number of corresponding href must be equal."

        return dict(zip(components, hrefs))

    def init_components(self) -> None:
        stocks = dict()
        for stock, stock_href in self._stock_to_href_dict.items():
            stocks[stock] = Stock(stock_href)

        self.prepared_components = stocks
        return None

    @property
    def components(self) -> list:
        return list(self._stock_to_href_dict.keys())


class Stock:
    def __init__(self, stock_href: str):
        """"""
        self.stock_href = stock_href
        self.url = urllib.parse.urljoin("https://www.onvista.de/", self.stock_href)
        # get full name. e.g.: aktien/Deutsche-Post-Aktie-DE0005552004 -> Deutsche-Post-Aktie-DE0005552004
        self.fullname = self.stock_href.split("/")[2]

    def __call__(self, *args, **kwargs):
        self.fundamentals = self._fundamental_figures()
        self.technical = self._technical_figures()
        self.corporate_details = self._corporate_figures()

        return self

    def __repr__(self):
        cls_ = type(self).__name__
        fmt_repr = f"{cls_}('{self.stock_href}')"

        return fmt_repr

    def _get_data_frame_from_url(self, url: str) -> list:
        stock_url = urllib.parse.urljoin(url, self.fullname)
        logger.info(f"Calling pandas.read_html('{stock_url}')")
        data_frames = pd.read_html(stock_url, decimal=',', thousands='.')

        return data_frames

    def _fundamental_figures(self) -> list:
        url = "https://www.onvista.de/aktien/fundamental/"
        return self._get_data_frame_from_url(url)

    def _technical_figures(self) -> list:
        url = "https://www.onvista.de/aktien/technische-kennzahlen/"
        return self._get_data_frame_from_url(url)

    def _corporate_figures(self) -> dict:
        """master data information is not saved in table, thus pd.read_html returns empty result.
        Instead the master data is scraped manually and result returned in dictionary.
        """
        url = "https://www.onvista.de/aktien/unternehmensprofil/"
        request = requests.get(urllib.parse.urljoin(url, self.fullname))
        soup = bs4.BeautifulSoup(request.content, "html.parser")
        master_data = soup.find_all("article", attrs={"class": ["STAMMDATEN"]})

        def get_data_from_dt_dd(bs4_tag: bs4.element.Tag) -> dict:
            """get data from dt and dd tags"""
            dt_tag_text = [tag.text for tag in bs4_tag.find_all("dt")]
            dd_tag_text = [tag.text if '...' not in tag.text else tag.get("title") for tag in bs4_tag.find_all("dd")]

            assert len(dd_tag_text) == len(dt_tag_text), "number of labels and number of values must be equal."

            dict_data = dict(zip(dt_tag_text, dd_tag_text))

            return dict_data

        return get_data_from_dt_dd(master_data[0])

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
        # replace strings n.a.% from DataFrame column `Perf.`
        perf.loc[perf["Perf."] == "n.a.%", "Perf."] = np.nan
        # cast column Perf. from `object` to `float`.
        perf = perf["Perf."].str.replace("%", "").str.replace(".", "").str.replace(",", ".", 1).astype(np.float64) / 100

        return perf

    @property
    def market_capitalization(self) -> pd.Series:
        df_market_cap = self._market_capitalization_figures().T["Marktkapitalisierung in Mio. EUR"]
        # replace "-" with np.nan
        df_market_cap = df_market_cap.replace("-", np.nan)
        df_market_cap = df_market_cap.astype(np.float64)
        # remove NaNs
        df_market_cap = df_market_cap[~df_market_cap.isna()]

        return df_market_cap

    @property
    def dividend_yield(self) -> pd.Series:
        df_dividend = self._dividend_figures().T["Dividendenrendite"]

        return df_dividend

    @property
    def pe_ratio(self) -> pd.Series:
        """Price-To-Earnings-Ratio (P/E Ratio) (dt. Kurs-Gewinn-Verhaeltnis, KGV)."""
        df_pe_ratio = self._revenue_figures().T["KGV"].str.replace("-", "0").astype(np.float64)

        return df_pe_ratio

    @property
    def isin(self):
        # get isin, e.g.: aktien/Deutsche-Post-Aktie-DE0005552004 -> DE0005552004
        return self.stock_href.split("-")[-1]

    @property
    def perf_1y(self):
        return self._performance_figures().loc["1 Jahr"]

    @property
    def perf_5y(self):
        return self._performance_figures().loc["5 Jahre"]

    @property
    def sector(self):
        return self.corporate_details["Sektor"]

    @property
    def industry(self):
        return self.corporate_details["Branche"]

    @property
    def corporate(self):
        return self.corporate_details["Unternehmen"]


if __name__ == '__main__':
    dax = Index("einzelwerte/DAX-Index-20735")
    dax.init_components()
    bmw = dax.prepared_components["BMW"]
