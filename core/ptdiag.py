from time import time_ns

import ptdiag.core.config as cfg
from ptdiag.core.ptprocess import PTProcess

class PTDiag:
    """ Parallel Timing Diagram Controller """

    def __init__(self, console_width=cfg.CONSOLE_WIDTH):
        self._cw = console_width

        self._start = time_ns()
        self._processes = list()
    
    def spawn(self, name=""):
        """ Creates, stores, and returns a new PTProcess instance. """

        name = name or f"Process: {len(self._processes)}"
        ptp = PTProcess(name)
        self._processes.append(ptp)

        return ptp
    
    def __str__(self):
        """ Formats the timing diagram in a readable way. """

        s = ""
        current_time = time_ns()

        for ptp in self._processes:
            s += ptp.format(self._cw, self._start, current_time) + "\n"

        return s
        