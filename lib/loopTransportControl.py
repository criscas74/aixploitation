from lib.metronome.metronomeCounter import LoopMidiMetronomeCounter
import mido
import threading

class LoopTransportControl(object):
    def __init__(self, inportName=None, throughportName=None, beatsPerLoop=2, startOnLoopStart=True, stopOnLoopEnd=True, resetMetronomeOnStop=False):
        self.inport = mido.open_input(inportName) if inportName is not None else None
        self.throughport = mido.open_output(throughportName) if throughportName is not None else None

        self.startOnLoopStart = startOnLoopStart
        self.stopOnLoopEnd = stopOnLoopEnd
        self.resetMetronomeOnStop = resetMetronomeOnStop
        self.clockStarted = False
        self.started = False
        self.running = False
        self.lmm = LoopMidiMetronomeCounter(beatsPerLoop)
        self.lmm.reset()
        self.status = None
        self.loopPos = None
        self.currMidiMessage = None
        self.loopStatus = None

    def on_clock_start(self):
        pass  # print(self.loopPos)

    def on_start(self):
        pass  # print(self.loopPos)

    def on_stop(self):
        pass  # print(self.loopPos)

    def on_running(self):
        pass  # print(self.loopPos)

    def on_sleeping(self):
        pass  # print(self.loopPos)

    def on_stopping(self):
        pass  # print(self.loopPos)

    def on_starting(self):
        pass  # print(self.loopPos)

    def on_auto_finish(self):
        pass  # print(self.loopPos)

    def on_loop_start(self):
        pass

    def on_loop_end(self):
        pass

    def parseMessage(self, message):
        self.currMidiMessage = message
        if message.type == 'clock':
            self.loopPos = self.lmm.click()
            isLoopStart = isLoopEnd = False
            self.status = None
            if self.lmm.isBeginning():
                isLoopStart = True
                self.status = 'loop_start'
                self.on_loop_start()
            elif self.lmm.isEnd():
                isLoopEnd = True
                self.status = 'loop_end'
                self.on_loop_end()
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

        return self.status,self.currMidiMessage,self.loopPos

    def _run_proc(self):
        for message in self.inport:
            if self.throughport is not None:
                self.throughport.send(message)
            self.parseMessage(message)
            self.loopStatus = self.loopPos['tick'] #self.status #self.get_status()

    def run(self, inport=None,throughport=None):
        if inport: self.inport = inport
        if throughport: self.throughport = throughport
        self._run_proc()

    def get_status(self):
        return {"status":self.status,"loopPosition":self.loopPos,"message":self.currMidiMessage}


class BackgroundLoopTransportControl(LoopTransportControl):
    def __init__(self, inportName=None, throughportName=None, beatsPerLoop=2, startOnLoopStart=True, stopOnLoopEnd=True, resetMetronomeOnStop=False):
        super(self.__class__, self).__init__(inportName, throughportName, beatsPerLoop, startOnLoopStart, stopOnLoopEnd, resetMetronomeOnStop)
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()


if __name__ == '__main__':
    import sys
    from rtmidi.midiutil import open_midiinput

    # Prompts user for MIDI input port, unless a valid port number or name
    # is given as the first argument on the command line.
    # API backend defaults to ALSA on Linux.
    port = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        midiin, port_name = open_midiinput(port)
        midiin.ignore_types(sysex=False,
                            timing=True,
                            active_sense=False)
    except (EOFError, KeyboardInterrupt):
        sys.exit()

    inPort = mido.open_input(port_name)

    tc = LoopTransportControl(beatsPerLoop=2, startOnLoopStart=False, stopOnLoopEnd=False, resetMetronomeOnStop=False)
    tc.run(inPort)

    """
    inport_name = 'MIDI4x4 Midi In 1'
    throughport_name = 'MIDI4x4 Midi Out 1'
    am = BackgroundLoopTransportControl(inport_name,throughport_name)
    while 1:
        for i in [.1,1,3]:
            print(am.get_status())
            time.sleep(i)
    """