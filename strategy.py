import pandas as pd
from datetime import datetime


class Strategy:
    def __init__(self, stocks: list, year=datetime.now().year):
        self.stocks = stocks
        self.current_year = year


class Dogs(Strategy):

    def _prepare_strategy(self) -> None:
        columns = ["no.", "corporation", "isin", "market_capitalization", "sector",
                   "perf_1y", "perf_5y",
                   "DIVe", "PEe"]
        failed_downloads = list()
        # most figures are estimates and are found in their corresponding tables under YEARe, e.g. 2020e.
        YEARe = str(self.current_year) + "e"

        df = pd.DataFrame()
        for no, stock in enumerate(self.stocks, start=1):
            try:
                dividend_yield = stock.dividend_yield.loc[YEARe]
            except KeyError:
                print(stock.corporate.upper(), stock.isin, "KeyError")
                failed_downloads.append(stock)
                dividend_yield = "NaN"

            stock_df = pd.DataFrame([[no, stock.corporate, stock.isin, stock.market_capitalization.iloc[0],
                                      stock.sector, stock.perf_1y, stock.perf_5y,
                                      dividend_yield,
                                      stock.pe_ratio.loc[YEARe]]], columns=columns)
            df = df.append(stock_df)

        print(failed_downloads)
        self.dogs_df = df.set_index("no.")

        return None

    @property
    def dogs_result_df(self):
        if not hasattr(self, "dogs_df"):
            self._prepare_strategy()

        return self.dogs_df

