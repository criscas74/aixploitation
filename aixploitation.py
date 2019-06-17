from pprint import pprint as pp
import mido
import time
import pyaudio
import numpy as np

from lib.loopTransportControl import LoopTransportControl
from lib.playbackRecorder import Recorder,Player
from lib.drumifier import Drumifier

CHUNK = 512  # CHUNKS of bytes to read each time from mic
FORMAT =  pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

MODELS_DIR = "models/"
MODEL_NAME = 'groovae_2bar_tap_fixed_velocity'
MODEL_FILE = MODELS_DIR + "%s.tar"%MODEL_NAME

OUTDIR = "out/"
RECORDING_OUTFILE = OUTDIR + "recording.wav"

class Aixploitation(LoopTransportControl):
    def __init__(self,beatsPerLoop=2,startOnLoopStart=True,stopOnLoopEnd=True,resetMetronomeOnStop=False):
        super(self.__class__, self).__init__(beatsPerLoop,startOnLoopStart,stopOnLoopEnd,resetMetronomeOnStop)

        #import librosa
        #self.click,_ = librosa.load("out/click.wav",RATE)

        self.recording = None
        self.drumloop = None
        self.playingback = True

        self.recorder = Recorder()
        self.player = Player()
        self.drumifier = Drumifier(modelName=MODEL_NAME,modelFile=MODEL_FILE)

    def create_process(self):
        print("hi, I'm the process!", self.currMidiMessage, self.loopPos)
        result = self.drumifier.loopAudioDataToDrumAudioData(self.recording['data'])
        self.drumloop = result

    def on_clock_start(self):
        print("clockStart", self.currMidiMessage,self.loopPos)

    def on_start(self):
        self.recorder.start()
        print("Recorder start",self.currMidiMessage,self.loopPos)

    def on_stop(self):
        print("Recorder finish", self.currMidiMessage,self.loopPos)
        self.recording = self.recorder.stop()
        #self.recorder.save(filename=RECORDING_OUTFILE)
        #pp(self.recording)
        self.drumloop = self.drumifier.loopAudioDataToDrumAudioData(self.recording['data'])
        if self.drumloop is not None:
            #self.playingback = True
            print("supper's ready", self.currMidiMessage,self.loopPos)
        else:
            print("gosh could'nt create drumloop")

    def on_loop_start(self):
        #pp(self.recording)
        print("loopStart", self.currMidiMessage,self.loopPos)
        if self.drumloop is not None and self.playingback:
            #self.player.start(self.drumloop['data'])
            self.player.start(self.recording['data'])
            print("playback started", self.currMidiMessage,self.loopPos)


    def run(self, inPort, throughPort):
        precunit = None
        precbeat = None
        for message in inPort:
            throughPort.send(message)
            self.currMidiMessage = self.parseMessage(message)
            if self.loopPos['beat'] != precbeat:
                print("---------- BEAT %s ----------"%self.loopPos['beat'])
                #self.player.start(self.click)
                precbeat = self.loopPos['beat']

            if self.loopPos['unit'] != precunit:
                pp(self.loopPos['unit'])
                precunit = self.loopPos['unit']





if __name__ == '__main__':
    import sys
    from rtmidi.midiutil import open_midiport

    # Prompts user for MIDI input port, unless a valid port number or name
    """
    in_name = sys.argv[1] if len(sys.argv) > 1 else None
    out_name = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        _,inport_name = open_midiport(in_name,type_="input")
        _,throughport_name = open_midiport(out_name, type_="output")
    except (EOFError, KeyboardInterrupt):
        sys.exit()
    """

    inport_name = 'MIDI4x4 Midi In 1'
    throughport_name = 'MIDI4x4 Midi Out 1'

    beatsPerLoop = 2

    print("Opening midi connection")
    inport  = mido.open_input(inport_name)
    throughport = mido.open_output(throughport_name)

    print("Initializing")
    aix = Aixploitation(beatsPerLoop)

    print("Start")
    aix.run(inport,throughport)
