import tkinter as tk
import itertools

import tools
from indices import Index
from strategy import Dogs


class Choices(tk.Tk):
    def __init__(self):
        super().__init__()

        self.stock_index = {"DAX": "DAX-Index-20735",
                            "MDAX": "MDAX-Index-323547",
                            "SDAX": "SDAX-Index-324724",
                            "TecDAX": "TecDAX-Index-6623216",
                            "E-STOXX 50": "EURO-STOXX-50-Index-193736",
                            "Dow Jones": "Dow-Jones-Index-324977",
                            "S&P 500": "S-P-500-Index-4359526",
                            "Nikkei 225": "Nikkei-Index-60972397",
                            "Hang Seng": "Hang-Seng-Index-8313314", }

        self.choices_var = None
        self.chosen_indices = None  # encompasses chosen indices on starting frame
        self.frame_choices = self.create_starting_frame()

    def create_starting_frame(self):
        """TODO: probably replace checkbox button with radio button for performance reasons."""
        frame_choices = tk.Frame(master=self)
        frame_choices.pack()
        # create list of IntVar() to carry choices made on starting frame
        self.choices_var = [tk.IntVar() for i in range(len(self.stock_index))]
        # create the check button where text=name of index
        for i, index_name in enumerate(self.stock_index):
            ckbtn_index_name = tk.Checkbutton(frame_choices,
                                              text=index_name,
                                              variable=self.choices_var[i],
                                              command=self.call_indices)
            # align check buttons on frame
            ckbtn_index_name.grid(row=i, column=0, sticky=tk.W)

        btn_go = tk.Button(frame_choices, text="Go!", command=self.call_main_window)
        btn_go.grid(row=i+1, column=0, sticky=tk.EW)
        return frame_choices

    def call_indices(self):
        self.chosen_indices = list(itertools.compress(self.stock_index,
                                                 [choice.get() for choice in self.choices_var]
                                                 ))
        tools.logger.debug(self.chosen_indices)

    def call_main_window(self):
        """TODO: calls main window containing index->stock->key figures info."""
        if not self.chosen_indices:
            tools.logger.info("Index selection empty.")
            return None
        for index_name in self.chosen_indices:
            index_url = self.stock_index[index_name]
            self.testing(index_url)

    @staticmethod
    def testing(index_url):
        """TODO: replace testing code with call for second GUI containing index->stock->key figures info."""
        print("testing")
        tec = Index(index_url)
        tec.init_components()
        dax_stocks_dict = tec.prepared_components
        stocks_for_strategy = tools.multiprocess(lambda x: x(), list(dax_stocks_dict.values()))
        dogs = Dogs(stocks_for_strategy)
        res = dogs.dogs_result_df
        app = dogs.apply_dogs_strategy(res, 1.5)
        tools.export_df(app, "{}.xlsx".format(index_url))

        return None


if __name__ == '__main__':
    choices = Choices()
    choices.mainloop()
