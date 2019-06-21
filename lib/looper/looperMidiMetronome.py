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
                                            ppq=ppq)

        self.CONTROL_CHANGE_RULES = {
            9: self.start_recording
        }

    def start_recording(self):
        self.metroStatus.message = 'start_recording'

if __name__ == '__main__':
    import mido
    import time
    port = mido.open_output('test', virtual=True)

    m = LooperMidiMetronome(inport_name='test')
    m.run_in_background()

    start = mido.Message('start')
    stop = mido.Message('stop')
    clock = mido.Message('clock')
    change = mido.Message('control_change', control=9, value=127)

    messages = [start] * 1 + [clock] * 48 + [change] * 1 + [clock] * 3 + [stop]
    print(messages)

    for msg in messages:
        port.send(msg)
        time.sleep(.1)
        print(m.status)
