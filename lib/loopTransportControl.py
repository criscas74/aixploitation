from lib.midiMetronomeCounter import LoopMidiMetronomeCounter
import mido

class LoopTransportControl(object):
    def __init__(self, beatsPerLoop, startOnLoopStart=True, stopOnLoopEnd=True, resetMetronomeOnStop=False):
        self.startOnLoopStart = startOnLoopStart
        self.stopOnLoopEnd = stopOnLoopEnd
        self.resetMetronomeOnStop = resetMetronomeOnStop
        self.started = False
        self.running = False
        self.lmm = LoopMidiMetronomeCounter(beatsPerLoop)
        self.lmm.reset()
        self.status = None
        self.loopPos = None

    def on_finish(self):
        pass  # print(self.loopPos)

    def on_start(self):
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
        if message.type == 'clock':
            self.loopPos = self.lmm.click()
            isLoopStart = isLoopEnd = False
            if self.lmm.isBeginning():
                isLoopStart = True
                self.on_loop_start()
            elif self.lmm.isEnd():
                isLoopEnd = True
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
                    self.status = None
                    self.on_sleeping()
            else:
                if self.stopOnLoopEnd:
                    if isLoopEnd:
                        self.started = False
                        self.running = False
                        self.status = "stop"
                        if self.resetMetronomeOnStop:
                            self.lmm.reset()
                        self.on_finish()
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
                        self.on_finish()
        elif message.type == 'start':
            self.started = True
        elif message.type == 'stop':
            self.started = False

        return self.status

    def run(self, inPort):
        for message in inPort:
            ret = self.parseMessage(message)
            if ret is not None:
                print(ret)


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