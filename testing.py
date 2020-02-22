from indices import Index
from strategy import Dogs
import tools

dax = Index("einzelwerte/DAX-Index-20735")
dax.init_components()
dax_stocks_dict = dax.prepared_components
stocks_for_strategy = tools.multiprocess(lambda x: x(), list(dax_stocks_dict.values()))
dogs = Dogs(stocks_for_strategy)
res = dogs.dogs_result_df
tools.export_df(res, "dogs.html")
