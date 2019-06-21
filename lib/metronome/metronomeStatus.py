class LoopStatus(object):
    def __init__(self, last_tick=None):
        self._last_tick = last_tick
        self.tick = None
        self.unit = None
        self.measure = None
        self.running = False
        self.qpm = None
        self.message = None
        self.midi_message = None

    @property
    def loop_landmark(self):
        return "beginning" if self.tick == 0 else "end" if self.tick == self._last_tick else False

    def __repr__(self):
        return "{}({!r})".format(type(self),self.__dict__)