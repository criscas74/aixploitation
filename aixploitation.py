from pprint import pprint as pp
import mido
import time
import pyaudio
import numpy as np

from lib.looper.looperTransportControl import LooperTransportControl
from lib.playbackRecorder import Recorder,Player
from lib.drumifier import Drumifier

CHUNK = 512  # CHUNKS of bytes to read each time from mic
FORMAT =  pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

MODELS_DIR = "models/"
MODEL_NAME = 'groovae_2bar_tap_fixed_velocity'
MODEL_FILE = MODELS_DIR + "%s.tar"%MODEL_NAME
TEMPERATURE = 1

OUTDIR = "out/"
RECORDING_OUTFILE = OUTDIR + "recording.wav"


class Aixploitation(LooperTransportControl):
    def __init__(self,inport_name,throughport_name,measures_per_loop=2,temperature=TEMPERATURE):
        super(Aixploitation,self).__init__(inport_name=inport_name,
                                           throughport_name=throughport_name,
                                           measures_per_loop=measures_per_loop)

        self.original_recording = None
        self.drumloop = None
        self.drumloop_age = 0
        self.temperature = temperature

        self.recorder = Recorder()
        self.player = Player()
        self.drumifier = Drumifier(modelName=MODEL_NAME,modelFile=MODEL_FILE)

    def on_start_recording(self):
        self.recorder.start()
        print("Recorder starts")

    def on_stop_recording(self):
        print("Recorder finish")
        self.original_recording = self.recorder.stop()
        self.recorder.save(filename=RECORDING_OUTFILE)
        #pp(self.recording)
        self.generate_drumloop()

    def on_start_playback(self):
        print(self.drumloop_age)
        if self.drumloop_age > 3:
            self.generate_drumloop()
        if self.drumloop is not None:
            self.player.start(self.drumloop['data'])
            self.drumloop_age += 1
        else:
            print("ERROR: NO DATA TO PLAYBACK")

    def on_stop_playback(self): pass

    def generate_drumloop(self):
        drumloop = self.drumifier.loopAudioDataToDrumAudioData(self.original_recording['data'],temperature=self.temperature)
        if drumloop is not None:
            self.drumloop = drumloop
            self.drumloop_age = 0

if __name__ == '__main__':

    # python2 aixploitation.py "MIDI4x4 Midi In 1" "MIDI4x4 Midi Out 1"

    #inport_name = 'MIDI4x4 Midi In 1'
    #throughport_name = 'MIDI4x4 Midi Out 1'

    import sys
    from rtmidi.midiutil import open_midiport

    # Prompts user for MIDI input port, unless a valid port number or name
    inport_name = sys.argv[1] if len(sys.argv) > 1 else None
    throughport_name = sys.argv[2] if len(sys.argv) > 2 else None

    if inport_name is None:
        try:
            _, inport_name = open_midiport(inport_name, type_="input")
        except (EOFError, KeyboardInterrupt):
            sys.exit()

    if throughport_name is None:
        try:
            _,throughport_name = open_midiport(throughport_name, type_="output")
        except (EOFError, KeyboardInterrupt):
            sys.exit()

    print("Initializing")
    aix = Aixploitation(inport_name,throughport_name)
    print("Run "*10)
    aix.run()
