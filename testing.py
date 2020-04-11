from indices import Index
from strategy import Dogs
import tools

tec = Index("Dow-Jones-Index-324977")
tec.init_components()
dax_stocks_dict = tec.prepared_components
stocks_for_strategy = tools.multiprocess(lambda x: x(), list(dax_stocks_dict.values()))
dogs = Dogs(stocks_for_strategy)
res = dogs.dogs_result_df
app = dogs.apply_dogs_strategy(res, 1.5)
tools.export_df(app, "dow_jones.xlsx")
