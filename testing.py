from indices import Index
from strategy import Dogs
import tools

mdax = Index("einzelwerte/MDAX-Index-323547")
mdax.init_components()
dax_stocks_dict = mdax.prepared_components
stocks_for_strategy = tools.multiprocess(lambda x: x(), list(dax_stocks_dict.values()))
dogs = Dogs(stocks_for_strategy)
res = dogs.dogs_result_df
tools.export_df(res, "mdax.xlsx")
