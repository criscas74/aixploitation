from pprint import pprint as pp
import mido
import time
import pyaudio
import numpy as np

from lib.loopTransportControl import BackgroundLoopTransportControl
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

class Aixploitation(object):
    def __init__(self,inportName,throughportName,beatsPerLoop=2,startOnLoopStart=True,stopOnLoopEnd=True,resetMetronomeOnStop=False):

        #import librosa
        #self.click,_ = librosa.load("out/click.wav",RATE)

        self.transport = BackgroundLoopTransportControl(inportName=inportName,throughportName=throughportName,beatsPerLoop=beatsPerLoop)
        self.recording = None
        self.drumloop = None
        self.playingback = True
        self.unit = 0
        self.beat = 0
        self.status = None

        self.recorder = Recorder()
        self.player = Player()
        self.drumifier = Drumifier(modelName=MODEL_NAME,modelFile=MODEL_FILE)

    def on_clock_start(self):
        print("clockStart",self.transportStatus)

    def on_start(self):
        self.recorder.start()
        print("Recorder start",self.transportStatus)

    def on_stop(self):
        print("Recorder finish",self.transportStatus)
        self.recording = self.recorder.stop()
        #self.recorder.save(filename=RECORDING_OUTFILE)
        #pp(self.recording)
        self.drumloop = self.drumifier.loopAudioDataToDrumAudioData(self.recording['data'])

    def on_loop_start(self):
        #pp(self.recording)
        print("loopStart",self.transportStatus)
        if self.drumloop is not None and self.playingback:
            self.player.start(self.drumloop['data'])
            #self.player.start(self.recording['data'])
            print("playback started", self.transportStatus)

    def metronome(self,verbose=True):
        unit = self.transportStatus['loopPosition']['unit']
        beat = self.transportStatus['loopPosition']['beat']
        if beat != self.beat:
            self.beat = beat
            if verbose:
                print("---------- BEAT %s ----------" % beat)
            # self.player.start(self.click)
        if unit != self.unit:
            self.unit = unit
            if verbose:
                print(unit, self.drumloop,self.transportStatus)

    def run(self):
        while 1:
            self.transportStatus = self.transport.get_status()
            self.metronome()
            status = self.transportStatus['status']
            if status != self.status:
                self.status = status
                if status == 'clock_started':
                    self.on_clock_start()
                elif status == 'loop_start':
                    self.on_loop_start()
                elif status == 'start':
                    self.on_start()
                elif status == 'stop':
                    self.on_stop()
                #print(self.transport.get_status())
            time.sleep(.01)

    def OLD_run(self, inPort, throughPort):
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
                print(self.loopPos['unit'],self.drumloop)
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
    print("Initializing")
    aix = Aixploitation(inport_name,throughport_name,beatsPerLoop)
    aix.run()
