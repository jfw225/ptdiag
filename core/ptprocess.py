from time import time_ns

import ptdiag.core.config as cfg

class PTProcess:
    """ Parallel Timing Diagram Process """
    
    def __init__(self, name):
        self._name = name

        self._start = time_ns()
        self._pairs = list()
        self._latest_on = 0

    def on(self):
        """ Signals that process is running. """

        if self._latest_on != 0:
            return
        
        self._latest_on = time_ns()

    def off(self):
        """ Signals that process it not running. """

        if self._latest_on == 0:
            return

        self._pairs.append((self._latest_on, time_ns()))
        self._latest_on = 0
    
    def format(self, cw, ptds, ct):
        """ Formats this process's timing diagram. """

        duration = ct - ptds
        off_since = ptds
        
        if self._latest_on != 0:
            self._pairs.append((self._latest_on, ct))

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
        




