import pandas as pd
from datetime import datetime

from tools import logger


class Strategy:
    def __init__(self, stocks: list, year=datetime.now().year):
        self.stocks = stocks
        self.current_year = year


class Dogs(Strategy):

    def _prepare_strategy(self) -> list:
        columns = ["no.", "corporation", "isin", "market_capitalization", "sector",
                   "perf_1y", "perf_5y",
                   "DIVe", "PEe"]
        failed_downloads = list()
        # most figures are estimates and are found in their corresponding tables under YEARe, e.g. 2020e.
        YEARe = str(self.current_year) + "e"

        df = pd.DataFrame()
        for no, stock in enumerate(self.stocks, start=1):
            # unfortunately some stocks have irregular column names, e.g. 19/20 instead of expected 2019, 2020 resp.
            try:
                dividend_yield = stock.dividend_yield.loc[YEARe]
            except KeyError:
                failed_downloads.append(stock)
                dividend_yield = stock.dividend_yield.iloc[2]
            try:
                pe_ratio = stock.pe_ratio.loc[YEARe]
            except KeyError:
                failed_downloads.append(stock)
                pe_ratio = stock.pe_ratio.iloc[2]

            stock_df = pd.DataFrame([[no, stock.corporate, stock.isin, stock.market_capitalization.iloc[0],
                                      stock.sector, stock.perf_1y, stock.perf_5y,
                                      dividend_yield, pe_ratio]], columns=columns)
            df = df.append(stock_df)

        print(failed_downloads)
        self.dogs_df = df.set_index("no.")

        # return later as part of warning
        return failed_downloads

    def apply_dogs_strategy(self, data: pd.DataFrame):
        logger.info(f"Executing strategy Dog's of the Dow for year {self.current_year}.")
        df = data.copy()
        df["aggregate"] = (df["perf_1y"].fillna(0.)
                           + df["perf_5y"].fillna(0.)
                           + df["DIVe"].fillna(0.)) / 3
        df = df[df["market_capitalization"] / 1000 > 5]

        df = df.sort_values(by=["sector", "aggregate"])

        return df

    @property
    def dogs_result_df(self):
        if not hasattr(self, "dogs_df"):
            res = self._prepare_strategy()
            if res:
                logger.warning(f"Dividend Yield and PE_Ratio for {res} not found. Used fallback instead. It "
                               f"is advised to check actual values online.")

        return self.dogs_df

