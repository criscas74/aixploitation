from lib.looper.looperMidiMetronome import LooperMidiMetronome

class LooperTransportControl(object):
    def __init__(self,
                 inport_name=None,
                 throughport_name=None,
                 numerator=4,
                 denumerator=4,
                 ppq=24,
                 measures_per_loop=1,
                 start_on_loop_beginning=True,
                 stop_on_loop_end=True):

        self.start_on_loop_beginning = start_on_loop_beginning
        self.stop_on_loop_end = stop_on_loop_end
        self.transport_status = None

        self.metro = LooperMidiMetronome(inport_name=inport_name,
                                         throughport_name=throughport_name,
                                         numerator=numerator,
                                         denumerator=denumerator,
                                         ppq=ppq,
                                         measures_per_loop=measures_per_loop)
        self.metro.run_in_background()

        self.TRANSPORT_RULES = [
            (self.have_to_start,self.start_recording)
            (self.have_to_stop,self.stop_recording)
            (self.have_to_playback,self.playback)
        ]

    #### TRANSPORT RULES ####
    def have_to_start(self):
        return self.transport_status == 'asked_to_start_recording' \
               and (self.loop_position == 'beginning' or not self.start_on_loop_beginning)

    def have_to_stop(self):
        return self.transport_status == 'recording' \
               and (self.loop_position == 'end' and self.stop_on_loop_end)

    def have_to_playback(self):
        return self.transport_status == 'recording' \
               and (self.loop_position == 'end' and self.stop_on_loop_end)

    def start_recording(self): pass
    def stop_recording(self):pass
    def playback(self):pass


    def asked_to_start_recording(self):
        self.transport_status = 'asked_to_start_recording' if self.start_on_loop_beginning else 'recording'

    def update_status(self):
        self.metro_running = self.metro.status.running
        self.metro_message = self.metro.status.message
        self.loop_position = self.metro.status.loop_landmark
        self.loop_qpm = self.metro.status.qpm

    def is_must_start(self):
        return True

    def start_recoding(self):
        pass

    def transport(self):
        for rule,command in self.TRANSPORT_RULES:
            if rule():
                command()

    def react(self):
        self.transport()

    def run(self):
        while 1:
            self.update_status()
            self.react()
            print(self.transport_status)
            time.sleep(.01)






"""

    def parseMessage(self, message):

            if not self.running:
                if self.started:
                    if self.startOnLoopStart:
                        if isLoopStart:
                            self.running = True
                            self.status = "start"
                            self.on_start()
                        else:
                            self.status = 'starting'
                            self.on_starting()
                    else:
                        self.running = True
                        self.status = 'start'
                        self.lmm.reset()
                else:
                    self.on_sleeping()
            else:
                if self.stopOnLoopEnd:
                    if isLoopEnd:
                        self.started = False
                        self.running = False
                        self.status = "stop"
                        if self.resetMetronomeOnStop:
                            self.lmm.reset()
                        self.on_stop()
                    else:
                        self.status = 'autostopping'
                        self.on_auto_finish()
                else:
                    if self.started:
                        self.status = "running"
                        self.on_running()
                    else:
                        self.running = False
                        self.status = "stop"
                        if self.resetMetronomeOnStop:
                            self.lmm.reset()
                        self.on_stop()
        elif message.type == 'start':
            self.clockStarted = True
            self.lmm.reset()
            self.status = "clock_started"
            self.on_clock_start()
            self.loopPos = self.lmm.click()
        elif message.type == 'stop':
            self.started = False
            self.status = "stop_started"
        elif message.type == 'control_change' and message.control == 9:
            self.started = True
            self.status = "record_started"

        return self.status, self.currMidiMessage, self.loopPos

    def _run_proc(self):
        for message in self.inport:
            if self.throughport is not None:
                self.throughport.send(message)
            self.parseMessage(message)
            self.loopStatus = self.loopPos['tick']  # self.status #self.get_status()

    def run(self, inport=None, throughport=None):
        if inport: self.inport = inport
        if throughport: self.throughport = throughport
        self._run_proc()

    def get_status(self):
        return {"status": self.status, "loopPosition": self.loopPos, "message": self.currMidiMessage}

"""


if __name__ == '__main__':
    import mido
    import time
    port = mido.open_output('test', virtual=True)

    t = LooperTransportControl(inport_name='test')

    start = mido.Message('start')
    stop = mido.Message('stop')
    clock = mido.Message('clock')
    change = mido.Message('control_change', control=9, value=127)

    messages = [start] * 1 + [clock] * 48 + [change] * 1 + [clock] * 3 + [stop]
    print(messages)

    for msg in messages:
        port.send(msg)
        time.sleep(.1)
        print(t.status)