from pprint import pprint as pp
import mido
from mido.frozen import freeze_message
import time
import threading

from metronomeStatus import  MetronomeStatus
from metronomeCounter import MetronomeCounter

class MidiMessageParser():
    def __init__(self):
        self.MESSAGES_RULES = {
            'clock':            self.on_clock,
            'start':            self.on_start,
            'stop':             self.on_stop,
            'control_change':   self.on_control_change,
            'sysex':            self.on_sysex
        }

        self.message =  None

    def on_clock(self): pass
    def on_start(self): pass
    def on_stop(self): pass
    def on_control_change(self): pass
    def on_sysex(self):pass

    def check_and_apply(self,k,d):
        if k in d:
            d[k]()
        else:
            pass # TODO implement logging

    def parse_message(self,message):
        self.message = message
        self.check_and_apply(self.message.type, self.MESSAGES_RULES)


class MidiMetronome(MetronomeCounter):
    def __init__(self,
                 inport_name=None,
                 throughport_name=None,
                 numerator=4,
                 denumerator=4,
                 ppq=24,
                 measures_per_loop=1):
        super(MidiMetronome, self).__init__(numerator=numerator,
                                            denumerator=denumerator,
                                            ppq=ppq,
                                            measures=measures_per_loop)

        self.inport = mido.open_input(inport_name) if inport_name is not None else None
        self.throughport = mido.open_output(throughport_name) if throughport_name is not None else None

        self.midi_message = None
        self.mmp = MidiMessageParser()
        self.mmp.MESSAGES_RULES = {
            'clock':            self.metro_clock,
            'start':            self.metro_start,
            'stop':             self.metro_stop,
        }

        self.metroStatus = MetronomeStatus(self.last_tick)

    def run_in_background(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

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
        return self.metroStatus

    def click(self):
        self.metroStatus.qpm = 120 # TODO calculate bpm
        self.metroStatus.tick = next(self._ticks_cycle)
        self.metroStatus.unit = next(self._units_cycle)
        self.metroStatus.measure = next(self._measures_cycle)

    def react(self):
        self.metroStatus.message = None
        self.mmp.parse_message(self.midi_message)

    def run(self):
        for message in self.inport:
            self.midi_message = message
            self.metroStatus.tstamp = time.time()
            self.metroStatus.midi_message = freeze_message(message)
            if self.throughport is not None:
                self.throughport.send(message)
            self.react()
            self.metroStatus.running = self.started


if __name__ == '__main__':

    """
    port = mido.open_output('test', virtual=True)
    m =MidiMetronome(inport_name='test')
    m.run_in_background()

    start = mido.Message('start')
    stop = mido.Message('stop')
    clock = mido.Message('clock')
    change = mido.Message('control_change', control=9, value=127)

    messages = [start] * 1 + [clock] * 8 + [stop] * 1 + [clock] * 2 #+ [clock] * 24 * 8 + [stop] + [clock] * 48
    print(messages)

    for msg in messages:
        port.send(msg)
        time.sleep(.05)
        print(m.status.tick,m.status.unit,m.status.measure,m.status.loop_landmark,m.status.running,"-",m.message.type)
        #print(m.status)
    """


    inport_name = 'MIDI4x4 Midi In 1'
    m =MidiMetronome(inport_name=inport_name)
    m.run_in_background()

    while 1:
        time.sleep(.01)
        print( m.status.tick, m.status.unit, m.status.measure,
               m.status.loop_landmark, m.status.running, "-", m.message.type)
