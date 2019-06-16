from pprint import pprint as pp
import mido
import time
import pyaudio
import numpy as np

from lib.loopTransportControl import LoopTransportControl
from lib.playbackRecorder import Recorder,Player


CHUNK = 512  # CHUNKS of bytes to read each time from mic
FORMAT =  pyaudio.paFloat32
CHANNELS = 1
RATE = 44100



class Aixploitation(LoopTransportControl):
    def __init__(self,beatsPerLoop=2,startOnLoopStart=True,stopOnLoopEnd=True,resetMetronomeOnStop=False):
        super(self.__class__, self).__init__(beatsPerLoop,startOnLoopStart,stopOnLoopEnd,resetMetronomeOnStop)
        self.recording = None

        self.recorder = Recorder()
        self.player = Player()

    def on_start(self):
        self.recorder.start()

    def on_finish(self):
        self.recording = self.recorder.stop()
        pp(self.recording)

    def on_loop_start(self):
        pp(self.recording)
        if self.recording is not None:
            self.player.start(self.recording['data'])

    def run(self, inPort, throughPort):
        for message in inPort:
            throughPort.send(message)
            ret = self.parseMessage(message)
            if ret is not None:
                print(ret)




if __name__ == '__main__':
    import sys
    from rtmidi.midiutil import open_midiport

    # Prompts user for MIDI input port, unless a valid port number or name
    # is given as the first argument on the command line.
    # API backend defaults to ALSA on Linux.
    in_name = sys.argv[1] if len(sys.argv) > 1 else None
    out_name = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        _,inport_name = open_midiport(in_name,type_="input")
        _,throughport_name = open_midiport(out_name, type_="output")
    except (EOFError, KeyboardInterrupt):
        sys.exit()

    beatsPerLoop = 2

    print("Opening midi connection")
    inport  = mido.open_input(inport_name)
    throughport = mido.open_output(throughport_name)

    print("Initializing")
    aix = Aixploitation(beatsPerLoop)

    print("Start")
    aix.run(inport,throughport)
