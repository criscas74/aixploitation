from pprint import pprint as pp
import time

from lib.looper.looperMidiMetronome import LooperMidiMetronome


class TransportStatus():
    def __init__(self):
        self.recorder = None
        self.player = None

    def __repr__(self):
        d = self.__dict__.copy()
        return "{}({!r})".format(type(self),d)


class LooperTransportControl(object):
    def __init__(self,
                 inport_name,
                 throughport_name=None,
                 measures_per_loop=1,
                 metronome=LooperMidiMetronome,
                 start_on_loop_beginning=True,
                 stop_on_loop_end=True,
                 autostart_playback=True):

        self.start_on_loop_beginning = start_on_loop_beginning
        self.stop_on_loop_end = stop_on_loop_end
        self.autostart_playback = autostart_playback

        self.loop_position = None
        self.measure_count = None
        self.unit_count = None
        self.loop_qpm = None

        self.transport_status = TransportStatus()
        self.playback_data = None

        self.metro = metronome(inport_name=inport_name,
                               throughport_name=throughport_name,
                               measures_per_loop=measures_per_loop)


        self.metro.run_in_background()
        self.metro_new = True
        self.metro_tstamp = None

        self.TRANSPORT_RULES = [
            (self.asked_to_start_recording,
             lambda: self.set_transport_status('recorder','asked_to_start')),

            (self.asked_to_start_playback,
             lambda: self.set_transport_status('player', 'asked_to_start')),

            (self.have_to_start_recording,self.start_recording),
            (self.have_to_stop_recording,self.stop_recording),

            (self.have_to_start_playback,self.start_playback),
            (self.have_to_stop_playback, self.stop_playback),
        ]

    #### TRANSPORT RULES ####

    ### CONDITIONS
    asked_to_start_recording = lambda(self): self.metro_new and self.metro_message == 'start_recording'
    asked_to_start_playback = lambda(self): self.metro_new and self.metro_message == 'start_playback'



    def have_to_start_recording(self):
        return self.metro_new \
               and (
                       self.transport_status.recorder == 'asked_to_start'
                       and (self.loop_position == 'beginning' or not self.start_on_loop_beginning)
               )

    def have_to_stop_recording(self):
        return self.metro_new \
               and (
                    self.transport_status.recorder == 'recording'
                    and (self.loop_position == 'end' and self.stop_on_loop_end)
                )

    def have_to_start_playback(self):
        return self.metro_new \
               and (
                       self.playback_data is not None
                       and (self.loop_position == 'beginning' or not self.start_on_loop_beginning)
                       and (
                               self.transport_status.player == 'asked_to_start'
                               or (self.autostart_playback and self.transport_status.player != 'playing')
                            )
               )

    def have_to_stop_playback(self):
        return self.metro_new \
               and self.transport_status.player == 'playing' \
               and (self.loop_position == 'end' and self.stop_on_loop_end)

    ### ACTIONS
    def start_recording(self):
        self.on_start_recording()
        self.set_transport_status('recorder','recording') # now record for real!

    def stop_recording(self):
        self.on_stop_recording()
        self.playback_data = True
        self.set_transport_status('recorder','stopped')

    def start_playback(self):
        self.on_start_playback()
        self.set_transport_status('player','playing')

    def stop_playback(self):
        self.on_stop_playback()
        self.set_transport_status('player', 'stopped')


    ### EVENTS
    def on_start_recording(self): pass #only for testing purposes
    def on_stop_recording(self): pass
    def on_start_playback(self): pass
    def on_stop_playback(self): pass


    ### TRANSPORT FUNCTIONNALITIES
    def set_transport_status(self, attr, status):
        setattr(self.transport_status, attr, status)
        print(self.transport_status)

    def update_metro_status(self):
        self.metro_new = True
        status = self.metro.status

        self.metro_tstamp = status.tstamp
        self.metro_running = status.running
        self.metro_message = status.message
        self.metro_midi_message = status.midi_message

        self.loop_position = status.loop_landmark
        self.measure_count = status.measure
        self.unit_count = status.unit
        self.loop_qpm = status.qpm

    def apply_rules(self):
        for rule,command in self.TRANSPORT_RULES:
            if rule():
                command()

    def react(self):
        self.apply_rules()

    def run(self):
        while 1:
            old_measure = self.measure_count
            old_unit = self.unit_count
            old_loop_pos = self.loop_position

            if self.metro_tstamp != self.metro.status.tstamp:
                self.update_metro_status()
            else:
                self.metro_new = False

            if self.loop_position and self.loop_position != old_loop_pos:
                print("-"*100 + "\nLoop: %s"%self.loop_position)
            if self.measure_count != old_measure:
                print("Measure: %s"%self.measure_count)
            if self.unit_count != old_unit:
                print("Unit: %s"%self.metro.status.unit)

            self.react()
            time.sleep(.01)


if __name__ == '__main__':
    import mido
    import time

    #launch looperMidiMetronome
    inport_name = 'test'

    inport_name = 'MIDI4x4 Midi In 1'

    t = LooperTransportControl(inport_name=inport_name,measures_per_loop=2)
    print("START!")
    t.run()