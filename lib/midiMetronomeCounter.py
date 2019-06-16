from pprint import pprint as pp
import mido
import time

def cycler(seq):
    while seq:
        for element in seq:
            yield element

class MidiMetronomeCounter(object):
    def __init__(self,numerator=4,denumerator=4,ppq=24):
        self.tick = None

        self.ticks_per_unit = ppq / (denumerator / 4)
        self.ticks_per_whole = self.ticks_per_unit * numerator

        self._ticks = range(self.ticks_per_whole)
        self._units = [x // self.ticks_per_unit for x in self._ticks]

    def reset(self):
        self._ticks_cycle = cycler(self._ticks)
        self._units_cycle = cycler(self._units)
        self.listsLen = len(self._ticks)

    def click(self):
        self.tick = next(self._ticks_cycle)
        return {"tick":self.tick,"unit":next(self._units_cycle)}

    def isBeginning(self):
        return self.tick == 0 if self.tick is not None else None

    def isEnd(self):
        return self.tick == self.listsLen - 1 if self.tick is not None else None

class LoopMidiMetronomeCounter(MidiMetronomeCounter):
    def __init__(self,beatsPerLoop=2,numerator=4,denumerator=4,ppq=24):
        super(self.__class__, self).__init__(numerator,denumerator,ppq)
        self.ticks_per_loop = self.ticks_per_whole * beatsPerLoop

        self._ticks = range(self.ticks_per_loop)
        self._beats = [x // self.ticks_per_whole for x in self._ticks]
        self._units = [x // self.ticks_per_unit - y * numerator for x,y in zip(self._ticks,self._beats)]

    def reset(self):
        self._ticks_cycle = cycler(self._ticks)
        self._units_cycle = cycler(self._units)
        self._beats_cycle = cycler(self._beats)
        self.listsLen = len(self._ticks)

    def click(self):
        self.tick = next(self._ticks_cycle)
        return {"tick": self.tick, "unit": next(self._units_cycle), "beat": next(self._beats_cycle)}


if __name__ == '__main__':

    """
    mm = MidiMetronomeCounter(5,8) # tempo in 5/8
    for x in range(384):
        print(mm.click())
    """


    lmm = LoopMidiMetronomeCounter(2,5,4) # loop di 2 battute in 5/4
    lmm.reset()
    for x in range(384 * 4):
        if lmm.isBeginning():
            print("-"*100)
        if lmm.isEnd():
            print("="*100)
        print(lmm.click())

