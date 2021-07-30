import matplotlib.pyplot as plt
import numpy as np

from multiprocessing.managers import BaseManager, SyncManager
from multiprocessing import Process, Manager
from random import random
from pickle import dump

from time import time_ns, sleep

import ptdiag.core.config as cfg
from ptdiag.core.ptprocess import PTProcess

class PTDiag(BaseManager):
    """ Parallel Timing Diagram Controller """

    def __init__(self):
        self._start = time_ns()
        self._finish = None

        super().__init__(address=cfg.ADDRESS)

        self.m = Manager()
        self._ptp_map = self.m.dict()
        self.register("reg_proc", callable=self.reg_proc)
        
        Process(target=self.get_server().serve_forever, daemon=True).start()

        # self.figure, (self.ax_ptd, self.ax_lower) = plt.subplots(nrows=2)
        # self.lower_fig, axs = self.ax_lower.add_subplot(nrows=1, ncols=0)
        self.ax_ptd = plt.subplot2grid((2, 3), (0, 0), colspan=5)
        self.ax_edges = plt.subplot2grid((2, 3), (1, 0), colspan=1)
        self.ax_times = plt.subplot2grid((2, 3), (1, 1), colspan=1)
        self.ax_rates = plt.subplot2grid((2, 3), (1, 2), colspan=1)
        # self.ax_stats_table = plt.subplot2grid((2, 5), (1, 3), colspan=2)

    def reg_proc(self, name):
        """ Called when PTProcess is instantiated. Registers PTProcess 
        attributes in controller. """
        
        pairs = self.m.list()
        lt_on = self.m.Value("i", 0)
        self._ptp_map[name] = (pairs, lt_on)

        return (pairs, lt_on)

    def spawn(self, name=""):
        """ Creates, stores, and returns a new PTProcess instance. """

        name = name or f"Process: {len(self._ptp_map)}"
        ptp = PTProcess(name)

        return ptp
    
    def set_start(self):
        """ Sets the start time of the program. """

        self._start = time_ns()

    def set_finish(self):
        """ Sets the finish time of the program. """

        self._finish = time_ns()

    def graph_all(self, save=False):
        """ Generates each graph. """

        self.graph_ptd()
        self.graph_stats()
        self.table_stats()
        
        if not save:
            self.show()
        else:
            path = cfg.PLT.FIG_SAVE + ".pkl"
            print(f"Saving PTD to: {path}")
            figure = plt.gcf()
            dump(figure, open(path, "wb"))

    def show(self):
        """ Calls plt.show(). """

        plt.show()

    def create_ptp_lines(self, name, pairs, lt_on, ft, y):
        """ Creates the lines on the timing diagram for a PTProcess. """

        # Shallow copy of pairs
        pairs = [x for x in pairs]

        duration = ft - self._start
        off_since = self._start
        
        if lt_on != 0:
            pairs.append((lt_on, ft))

        color = (random(), random(), random())
        for ont, offt in pairs:
            self.ax_ptd.hlines(y, off_since, ont, color=color)
            self.ax_ptd.vlines(ont, y, y + 1, color=color)
            self.ax_ptd.hlines(y + 1, ont, offt, color=color)
            self.ax_ptd.vlines(offt, y, y + 1, color=color)
            off_since = offt
        
        self.ax_ptd.hlines(y, off_since, ft, color=color, label=name)

    def get_stats(self):
        """ Generates and returns PTD statistics. """

        self._finish = self._finish or time_ns()
        stats = list()
        for name, (pairs, lt_on) in self._ptp_map.items():
            if lt_on.value != 0:
                pairs.append((lt_on.value, self._finish))
            
            num_edges = len(pairs)
            time_on = time_off = 0

            off_since = self._start
            for ont, offt in pairs:
                time_off += ont - off_since
                time_on += offt - ont
                off_since = offt
            
            time_off += self._finish - off_since
            
            rate_on = num_edges / time_on if time_on else 0
            rate_off = num_edges / time_off if time_on else 0

            stats.append((name, num_edges, time_on, time_off, rate_on, rate_off))
        
        return stats

    def graph_ptd(self):
        """ Graphs the parallel timing diagram. """

        print("Generating PTD Graph...")
        # fig = plt.figure(cfg.PLT.PTD_ID)
        self._finish = self._finish or time_ns()

        y = 1.5 * len(self._ptp_map)
        for name, (pairs, lt_on) in self._ptp_map.items():
            self.create_ptp_lines(name, pairs, lt_on.value, self._finish, y)
            y -= 1.5
        
        self.ax_ptd.set_ylabel("High/Low")
        self.ax_ptd.set_xlabel("Unix Time (ns)")
        self.ax_ptd.legend()


    def graph_stats(self):
        """ Displays the PTD statistics as a bar graph. """

        print("Generating PTD Stats Bar Graph...")

        stats = self.get_stats()
        names, num_edges, times_on, times_off, rates_on, rates_off = zip(*stats)
        
        x = np.arange(len(names))
        width = 0.5

        # Edges
        edges_bar = self.ax_edges.bar(x, num_edges, width)
        self.ax_edges.bar_label(edges_bar, padding=2)
        self.ax_edges.set_ylabel("n")
        self.ax_edges.set_xticks(x)
        self.ax_edges.set_xticklabels(names, rotation=45)
        self.ax_edges.set_title("Number of Edges")

        # Times
        times_on = np.around(np.array(times_on) / 1e9, decimals=2)
        times_off = np.around(np.array(times_off) / 1e9, decimals=2)
        times_on_bar = self.ax_times.bar(x - (width - .15) / 2, times_on, (width - .15), label="On")
        times_off_bar = self.ax_times.bar(x + (width - .15) / 2, times_off, (width - .15), label="Off")
        self.ax_times.bar_label(times_on_bar, padding=2)
        self.ax_times.bar_label(times_off_bar, padding=2)
        self.ax_times.set_ylabel("Time (s)")
        self.ax_times.set_xticks(x)
        self.ax_times.set_xticklabels(names, rotation=45)
        self.ax_times.set_title("Time Spent")
        self.ax_times.legend()

        # Rates
        rates_on = np.around(np.array(rates_on) * 1e9, decimals=2)
        rates_off = np.around(np.array(rates_off) * 1e9, decimals=2)
        rates_on_bar = self.ax_rates.bar(x - (width - .15) / 2, rates_on, (width - .15), label="On")
        rates_off_bar = self.ax_rates.bar(x + (width - .15) / 2, rates_off, (width - .15), label="Off")
        self.ax_rates.bar_label(rates_on_bar, padding=2)
        self.ax_rates.bar_label(rates_off_bar, padding=2)
        self.ax_rates.set_ylabel("Rate (edge / s)")
        self.ax_rates.set_xticks(x)
        self.ax_rates.set_xticklabels(names, rotation=45)
        self.ax_rates.set_title("Edge Rate")
        self.ax_rates.legend()

        # fig.tight_layout()

        
    def table_stats(self):
        """ Creates a table containing PTD statistics. """

        print("Generating PTD Stats Table...")


    def __str__(self):
        """ Formats the timing diagram statistics in a readable way. """

        s = ""
        for name, num_edges, time_on, time_off, rate_on, rate_off in self.get_stats():
            s += f"{name}: {num_edges} edges | {time_on/1e9} s on, {time_off/1e9} s off"
            s += f" | {rate_on*1e9} e/s on, {rate_off*1e9} e/s off\n"

        return s
        