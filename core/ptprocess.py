from multiprocessing.managers import BaseManager, SyncManager
from multiprocessing import Manager
from time import time_ns

import ptdiag.core.config as cfg

class PTProcess(BaseManager):
    """ Parallel Timing Diagram Process """
    
    def __init__(self, name, ptp_id=None):
        self._name = name
        self._id = ptp_id
        self._start = time_ns()

        super().__init__(address=cfg.ADDRESS)
        self.register("reg_proc")

        self.connect()
        self._pairs, self._latest_on = self.reg_proc(self._name, self._id)._getvalue()

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



