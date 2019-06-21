import time

class MetronomeStatus(object):
    def __init__(self, last_tick=None):
        self._last_tick = last_tick
        self.tick = None
        self.unit = None
        self.measure = None
        self.running = False
        self.qpm = None
        self.message = None
        self.midi_message = None
        self.tstamp = time.time()

    @property
    def loop_landmark(self):
        return "beginning" if self.tick == 0 else "end" if self.tick == self._last_tick else False

    def __repr__(self):
        d = self.__dict__.copy()
        d['loop_landmark'] = self.loop_landmark
        return "{}({!r})".format(type(self),d)