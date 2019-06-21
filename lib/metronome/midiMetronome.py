from pprint import pprint as pp
import mido
import time
import threading

from lib.metronome.metronomeStatus import  MetronomeStatus
from lib.metronome.metronomeCounter import MetronomeCounter

class MidiMetronome(MetronomeCounter):
    def __init__(self,
                 inport_name=None,
                 throughport_name=None,
                 numerator=4,
                 denumerator=4,
                 ppq=24,
                 measures_per_loop=1):
        super(MidiMetronome, self).__init__(numerator,
                                             denumerator,
                                             ppq,
                                             measures_per_loop)

        self.inport = mido.open_input(inport_name) if inport_name is not None else None
        self.throughport = mido.open_output(throughport_name) if throughport_name is not None else None

        self.message = None

        self.MESSAGES_RULES = {
            'clock':            self.metro_clock,
            'start':            self.metro_start,
            'stop':             self.metro_stop,
            'control_change':   self.control_change,
            'sysex':            self.sysex
        }
        self.CONTROL_CHANGE_RULES = {}
        self.SYSEX_RULES = {}

    def run_in_background(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    ### MIDI PARSING LOGIC ###

    def check_and_apply(self,k,d):
        if k in d:
            d[k]()
        else:
            pass # TODO implement logging

    def parse_message(self):    self.check_and_apply(self.message.type, self.MESSAGES_RULES)
    def control_change(self):   self.check_and_apply(self.message.control,self.CONTROL_CHANGE_RULES)
    def sysex(self):            self.check_and_apply(self.message.sysex, self.SYSEX_RULES)

    def metro_clock(self):
        if self.started:
            self.click()

    def metro_start(self):
        self.started = True
        self.reset()

    def metro_stop(self):
        self.started = False

    ### METRONOME LOGIC ###

    @property
    def status(self):
        return self.loopStatus

    def click(self):
        self.loopStatus.qpm = 120 # TODO calculate bpm
        self.loopStatus.tick = next(self._ticks_cycle)
        self.loopStatus.unit = next(self._units_cycle)
        self.loopStatus.measure = next(self._measures_cycle)
        self.loopStatus.running = self.started

    def react(self):
        self.parse_message()

    def run(self):
        for message in self.inport:
            self.loopStatus = MetronomeStatus(self.last_tick)
            self.message = message
            self.loopStatus.midi_message = message
            if self.throughport is not None:
                self.throughport.send(self.message)
            self.react()

if __name__ == '__main__':
    port = mido.open_output('test', virtual=True)
    m =MidiMetronome(inport_name='test')
    m.run_in_background()
    msg = mido.Message('start')
    pp(msg)
    port.send(msg)

    while 1:
        msg = mido.Message('clock')
        pp(msg)
        port.send(msg)
        time.sleep(.1)
        print(m.status)