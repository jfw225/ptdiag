from multiprocessing.managers import BaseManager, SyncManager
from multiprocessing import Manager
from time import time_ns

import ptdiag.core.config as cfg

class PTProcess(BaseManager):
    """ Parallel Timing Diagram Process """
    
    def __init__(self, name):
        self._name = name
        self._start = time_ns()

        super().__init__(address=cfg.ADDRESS)
        self.register("reg_proc")

        # self.man = Manager()
        # self._pairs = self.man.list()
        # self._latest_on = self.man.Value("i", 0)

        self.connect()
        self._pairs, self._latest_on = self.reg_proc(self._name)._getvalue()

    def on(self):
        """ Signals that process is running. """

        if self._latest_on.value != 0:
            return
        
        self._latest_on.value = time_ns()

    def off(self):
        """ Signals that process it not running. """

        if self._latest_on.value == 0:
            return

        self._pairs.append((self._latest_on.value, time_ns()))
        self._latest_on.value = 0
    
    def format(self, cw, ptds, ct):
        """ Formats this process's timing diagram. """

        duration = ct - ptds
        off_since = ptds
        
        if self._latest_on.value != 0:
            self._pairs.append((self._latest_on.value, ct))

        s = ""
        for ont, offt in self._pairs:
            n = int(((ont - off_since) / duration) * cw)
            s += " " * n
            n = int(((offt - ont) / duration) * cw)
            s += cfg.BLOCK * n
            off_since = offt
        
        n = int(((ct - off_since) / duration) * cw)
        s += " " * n

        return s + "|: " + self._name
        




