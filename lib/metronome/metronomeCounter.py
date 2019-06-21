from pprint import pprint as pp
from loopStatus import LoopStatus

class MidiMetronomeCounter(object):
    def __init__(self, numerator=4, denumerator=4, ppq=24, measures=1):
        self.started = False

        self.ticks_per_unit = ppq / (denumerator / 4)
        self.ticks_per_whole = self.ticks_per_unit * numerator
        self.ticks_per_loop = self.ticks_per_whole * measures
        self.last_tick = self.ticks_per_loop - 1

        self._ticks = range(self.ticks_per_loop)
        self._measures = [x // self.ticks_per_whole for x in self._ticks]
        self._units = [x // self.ticks_per_unit - y * numerator for x, y in zip(self._ticks, self._measures)]

        self.loopStatus = LoopStatus(self.last_tick)

        self._ticks_cycle = self._units_cycle = self._measures_cycle = None

        self.reset()

    @staticmethod
    def cycler(seq):
        while seq:
            for element in seq:
                yield element

    def reset(self):
        self._ticks_cycle = self.cycler(self._ticks)
        self._units_cycle = self.cycler(self._units)
        self._measures_cycle = self.cycler(self._measures)

    def click(self):
        self.loopStatus.tick = next(self._ticks_cycle)
        self.loopStatus.unit = next(self._units_cycle)
        self.loopStatus.measure = next(self._measures_cycle)


if __name__ == '__main__':
    lmm = MidiMetronomeCounter(2,5,4) # loop di 2 battute in 5/4
    lmm.reset()
    for x in range(384 * 4):
        lmm.click()
        status = lmm.loopStatus
        if status.loop_landmark == 'beginning':
            print("-"*100)
        elif status.loop_landmark == 'end':
            print("="*100)
        print(status)
