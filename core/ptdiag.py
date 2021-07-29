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

    def __init__(self, console_width=cfg.CONSOLE_WIDTH):
        self._cw = console_width
        self._start = time_ns()

        super().__init__(address=cfg.ADDRESS)

        self.m = Manager()
        self._ptp_map = self.m.dict()
        self.register("reg_proc", callable=self.reg_proc)
        
        Process(target=self.get_server().serve_forever, daemon=True).start()

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
    
    def format(self, name, pairs, lt_on, ct):
        """ Formats a process's timing diagram. """

        # Shallow copy of pairs
        pairs = [x for x in pairs]

        duration = ct - self._start
        off_since = self._start
        
        if lt_on != 0:
            pairs.append((lt_on, ct))

        s = ""
        # for ont, offt in self._pairs:
        for ont, offt in pairs:
            n = int(((ont - off_since) / duration) * self._cw)
            s += " " * n
            n = int(((offt - ont) / duration) * self._cw)
            s += cfg.BLOCK * n
            off_since = offt
        
        n = int(((ct - off_since) / duration) * self._cw)
        s += " " * n

        return s + "|: " + name

    def format_y(self, name, pairs, lt_on, ct, y):
        """ Formats the y positions on the timing diagram for a PTProcess. """

        # Shallow copy of pairs
        pairs = [x for x in pairs]

        duration = ct - self._start
        off_since = self._start
        
        if lt_on != 0:
            pairs.append((lt_on, ct))

        color = (random(), random(), random())
        for ont, offt in pairs:
            plt.hlines(y, off_since, ont, color=color)
            plt.vlines(ont, y, y + 1, color=color)
            plt.hlines(y + 1, ont, offt, color=color)
            plt.vlines(offt, y, y + 1, color=color)
            off_since = offt
        
        plt.hlines(y, off_since, ct, color=color, label=name)


    def graph(self, save=False):
        """ Graphs the timing diagram. """

        current_time = time_ns()
        x = np.arange(self._start, current_time, dtype=np.int8)

        y = 0
        for name, (pairs, lt_on) in self._ptp_map.items():
            self.format_y(name, pairs, lt_on.value, current_time, y)
            y += 1.5
        
        plt.legend(loc="best")

        if save:
            fig = plt.gcf()
            dump(fig, open("figure.pkl", "wb"))
        else:
            plt.show()

    def __str__(self):
        """ Formats the timing diagram in a readable way. """

        s = ""
        current_time = time_ns()

        for name, (pairs, lt_on) in self._ptp_map.items():
            s += self.format(name, pairs, lt_on.value, current_time) + "\n"
        # for ptp in self._processes:
        #     s += ptp.format(self._cw, self._start, current_time) + "\n"

        return s
        