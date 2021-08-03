from multiprocessing.managers import BaseManager, SyncManager
from multiprocessing import Manager
from time import time_ns

import ptdiag.core.config as cfg

class PTProcess(BaseManager):
    """ Parallel Timing Diagram Process """
    
    class KWARGS:
        EXCLUDE_FROM_GRAPH = "exclude_from_graph"

    def __init__(self, name, ptp_id=None, **kwargs):
        """ Valid keyword arguments:
        exclude_from_graph -- excludes process from graph
        """

        self._name = name
        self._id = ptp_id
        self._extra = kwargs
        
        super().__init__(address=cfg.ADDRESS)
        self.register("reg_proc")

        self.connect()
        self._pairs, self._latest_on = self.reg_proc(self._name, self._id, self._extra)._getvalue()

        self.start()

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

    def start(self):
        """ Adds the starting time for the controller. """

        ct = time_ns()
        if len(self._pairs) > 0:
            self._pairs[0] = (ct, ct)
        else:
            self._pairs.append((ct, ct))

    def finish(self):
        """ Sets the finish time for the controller. """

        if self._latest_on.value != 0:
            self.off()
        
        assert len(self._pairs) > 0, f"Error: Tried to call finished before any pairs were created. | Name: {self._name}, Pairs: {pairs}"
        pair = self._pairs[0]
        self._pairs[0] = (pair[0], time_ns())

    def __del__(self):
        """ Set's finish time on object destruction. """

        try: 
            self.finish()
        except:
            pass
