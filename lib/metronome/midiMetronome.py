from pprint import pprint as pp
import mido
from mido.frozen import freeze_message
import time
import threading
from collections import deque

from metronomeStatus import  MetronomeStatus
from metronomeCounter import MetronomeCounter


"""
TODO:
- se no input usa clock interno
    - se no qpm entra in modo tap tempo (magari con un pedale nel g2m)
    - se no tap apri audio in e fai beat detection
    
- aspetta di avere un bpm di riferimento prima di partire

LOGGING!
"""

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

        self.ppq = ppq
        self.qpm_min_samples = ppq * 8
        self.queue = deque(maxlen=self.qpm_min_samples * 2)
        self.last_bpm = None

        self.midi_message = None
        self.MESSAGES_RULES = {
            'clock':            self.metro_clock,
            'start':            self.metro_start,
            'stop':             self.metro_stop,
        }

        self.metro_status = MetronomeStatus(self.last_tick)

    @property
    def qpm(self):
        if len(self.queue) >= self.ppq:
            return (60. / ( (self.queue[-1] - self.queue[0]) / len(self.queue) * self.ppq))

    # FOR MANAGING MIDI RULES
    def check_and_apply(self,k,d):
        if k in d:
            d[k]()
        else:
            pass # TODO implement logging

    def parse_midi_message(self,message):
        self.message = message
        self.check_and_apply(self.message.type, self.MESSAGES_RULES)

    def metro_clock(self):
        self.queue.append(time.time())
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
        return self.metro_status

    def click(self):
        if self.metro_status.qpm is not None:
            self.metro_status.tick = next(self._ticks_cycle)
            self.metro_status.unit = next(self._units_cycle)
            self.metro_status.measure = next(self._measures_cycle)

    def react(self):
        self.metro_status.message = None
        self.parse_midi_message(self.midi_message)

    # BLOCKING RUN
    def run(self):
        for message in self.inport:
            self.midi_message = message
            self.metro_status.tstamp = time.time()
            self.metro_status.qpm = self.qpm
            self.metro_status.midi_message = freeze_message(message)
            if self.throughport is not None:
                self.throughport.send(message)
            self.react()
            self.metro_status.running = self.started

    # USE THREADING FOR RUNNING IN BACKGROUND
    def run_in_background(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()


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
               m.status.loop_landmark, m.status.running, m.status.qpm, "-", m.midi_message.type if m.midi_message is not None else None)
