from lib.metronome.midiMetronome import MidiMetronome

class LooperMidiMetronome(MidiMetronome):
    def __init__(self,
                 inport_name=None,
                 throughport_name=None,
                 numerator=4,
                 denumerator=4,
                 ppq=24,
                 measures_per_loop=2):
        super(LooperMidiMetronome, self).__init__(inport_name=inport_name,
                                                  throughport_name=throughport_name,
                                                  numerator=numerator,
                                                  denumerator=denumerator,
                                                  measures_per_loop=measures_per_loop,
                                                  ppq=ppq)

        self.mmp.MESSAGES_RULES['control_change'] = lambda: self.mmp.check_and_apply(self.midi_message.control,
                                                                                     self.CONTROL_CHANGE_RULES)

        self.CONTROL_CHANGE_RULES = {
            9: self.start_recording
        }

    def start_recording(self):
        self.metroStatus.message = 'start_recording'

if __name__ == '__main__':
    import mido
    import time

    """
    port = mido.open_output('test', virtual=True)

    m = LooperMidiMetronome(inport_name='test')
    m.run_in_background()

    start = mido.Message('start')
    stop = mido.Message('stop')
    clock = mido.Message('clock')
    change = mido.Message('control_change', control=9, value=127)

    messages = [start] * 1 + [clock] * 48 + [change] * 1 + [clock] * 2 #+ [clock] * 24 * 8 + [stop] + [clock] * 48
    print(messages)

    while  1:
        for msg in messages:
            port.send(msg)
            time.sleep(.05)
            print(m.status.tick, m.status.unit, m.status.measure, m.status.loop_landmark, m.status.running, "-",
                  m.message.type)
            #print(m.status)

    """
    inport_name = 'MIDI4x4 Midi In 1'
    m = MidiMetronome(inport_name=inport_name)
    m.run_in_background()

    while 1:
        time.sleep(.01)
        print(m.status.tick, m.status.unit, m.status.measure,
              m.status.loop_landmark, m.status.running, "-", m.message.type)