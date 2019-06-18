from pprint import pprint as pp

import librosa
import copy
import numpy as np
from magenta import music as mm
from magenta.models.music_vae import configs
from magenta.models.music_vae.trained_model import TrainedModel
from magenta.music import midi_synth
from magenta.protobuf import music_pb2


def combine_sequences_with_lengths(sequences, lengths):
    seqs = copy.deepcopy(sequences)
    total_shift_amount = 0
    for i, seq in enumerate(seqs):
        if i == 0:
            shift_amount = 0
        else:
            shift_amount = lengths[i - 1]
        total_shift_amount += shift_amount
        if total_shift_amount > 0:
            seqs[i] = mm.sequences_lib.shift_sequence_times(seq, total_shift_amount)
    combined_seq = music_pb2.NoteSequence()
    for i in range(len(seqs)):
        tempo = combined_seq.tempos.add()
        tempo.qpm = seqs[i].tempos[0].qpm
        tempo.time = sum(lengths[0:i - 1])
        for note in seqs[i].notes:
            combined_seq.notes.extend([copy.deepcopy(note)])
    return combined_seq

# If a sequence has notes at time before 0.0, scootch them up to 0
def start_notes_at_0(s):
    for n in s.notes:
        if n.start_time < 0:
            n.end_time -= n.start_time
            n.start_time = 0
    return s

def mix_tracks(y1, y2, stereo=False):
    l = max(len(y1), len(y2))
    y1 = librosa.util.fix_length(y1, l)
    y2 = librosa.util.fix_length(y2, l)

    if stereo:
        return np.vstack([y1, y2])
    else:
        return y1 + y2

####################
# CUSTOM FUNCTS
####################
def changeInstrument(sequence,instrument):
  subsequence = music_pb2.NoteSequence()
  subsequence.CopyFrom(sequence)
  del subsequence.notes[:]
  for note in sequence.notes:
    new_note = subsequence.notes.add()
    new_note.CopyFrom(note)
    new_note.instrument = instrument
  return subsequence

##############################
# CORE FUNCTIONS
##############################

def extract_audio_features(y,sr,tempo):
    duration = librosa.get_duration(y,sr)
    onset_env = librosa.onset.onset_strength(y, sr=sr)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, max_tempo=180)[0] if tempo is None else tempo
    onset_times = librosa.onset.onset_detect(y, sr, units='time')
    onset_frames = librosa.onset.onset_detect(y, sr, units='frames')
    onset_strengths = librosa.onset.onset_strength(y, sr)[onset_frames]
    normalized_onset_strengths = onset_strengths / np.max(onset_strengths)
    onset_velocities = np.int32(normalized_onset_strengths * 127)
    return {'duration':duration,'tempo':tempo,'onset_times':onset_times,'onset_frames':onset_frames,'onset_strengths':onset_strengths,'onset_velocities':onset_velocities}

def make_tap_sequence(tempo, onset_times, onset_frames, onset_velocities,
                      velocity_threshold, start_time, end_time):
    note_sequence = music_pb2.NoteSequence()
    note_sequence.tempos.add(qpm=tempo)
    for onset_vel, onset_time in zip(onset_velocities, onset_times):
        if onset_vel > velocity_threshold and onset_time >= start_time and onset_time < end_time:  # filter quietest notes
            start = onset_time - start_time
            end = start + 0.01
            note_sequence.notes.add(
                instrument=9, pitch=42, is_drum=True,
                velocity=onset_vel,  # model will use fixed velocity here
                start_time=start,
                end_time=end
            )
            #print("add - start: %s, end: %s, velocity: %s"%(start,end,onset_vel))
        else:
            #print("discard")
            pass
    return note_sequence

def drumify(s, model, temperature=.1):
    try:
        encoding, mu, sigma = model.encode([s])
        decoded = model.decode(encoding, length=32, temperature=temperature)
        return decoded[0]
    except Exception as e:
        print(str(e))

def seq2audio(s,sr,sf2_path=None):
    return librosa.util.normalize(midi_synth.fluidsynth(s, sample_rate=sr,sf2_path=sf2_path))


RATE = 44100
MODELS_DIR = "../models/"
MODEL_NAME = 'groovae_2bar_tap_fixed_velocity'
MODEL_FILE = MODELS_DIR + "%s.tar"%MODEL_NAME

VELOCITY_TRESHOLD = 30
QUANTIZATION_STEP = 4 #1/16
TEMPERATURE = .5

class Drumifier():
    def __init__(self,modelName=MODEL_NAME,modelFile=MODEL_FILE):
        self.model = TrainedModel(configs.CONFIG_MAP[modelName], 1, checkpoint_dir_or_path=modelFile)
        self.temperature = TEMPERATURE
        self.inAudioLoopData = np.array([])
        self.inAudioLoopFeatures = dict()
        self.rate = RATE
        self.tapSequence = None
        self.qpm = None
        self.drumSequence = None
        self.drumAudio = None

    def setAudioLoopdata(self,inData,rate=None):
        self.inAudioLoopData = inData
        self.rate = rate if rate is not None else RATE

    def extractAudioFeatures(self):
        self.inAudioLoopFeatures = extract_audio_features(self.inAudioLoopData,self.rate,self.qpm)
        self.qpm = self.inAudioLoopFeatures['tempo']
        return self.inAudioLoopFeatures

    def makeTapSequenceFromAudioFeatures(self,velocityTreshold=None):
        self.tapSequence = make_tap_sequence(
            self.qpm,
            self.inAudioLoopFeatures['onset_times'],
            self.inAudioLoopFeatures['onset_frames'],
            self.inAudioLoopFeatures['onset_velocities'],
            np.average(self.inAudioLoopFeatures['onset_velocities']) / 2 if velocityTreshold is None else velocityTreshold, #find better function!!!
            0, #start time
            self.inAudioLoopFeatures['duration'])
        return self.tapSequence

    def quantizeTapSequence(self,quantizationStep=QUANTIZATION_STEP):
        self.tapSequence = mm.quantize_note_sequence(self.tapSequence,quantizationStep)
        return self.tapSequence

    def drumify(self):
        print("Drumifying with temperature: %s"%self.temperature)
        self.drumSequence = drumify(self.tapSequence,self.model,self.temperature)
        return self.drumSequence

    def drumSeq2audio(self,sf2_path=None):
        self.drumAudio = seq2audio(self.drumSequence,self.rate,sf2_path)
        return self.drumAudio

    """def changeInstrument(self,instrument):
        self.drumSequence = changeInstrument(self.drumSequence,instrument)
        return self.drumSequence
        """

    def loopAudioDataToDrumAudioData(self,inData,quantize=True,quantizationSteps=QUANTIZATION_STEP,temperature=None): #,instrument=None):
        if temperature is not None:
            self.temperature = temperature
        self.setAudioLoopdata(inData)
        self.extractAudioFeatures()
        self.makeTapSequenceFromAudioFeatures()
        if quantize:
            self.quantizeTapSequence(quantizationSteps)
        self.drumify()
        if self.drumSequence is None:
            print("Something went terribly wrong: no drum sequence!!! - Fallbacking to tap sequence!")
            self.drumSequence = self.tapSequence

        #if instrument is not None:
        #    self.changeInstrument(instrument)

        self.drumSeq2audio()
        return {"data":self.drumAudio.astype('float32')}


if __name__ == '__main__':

    y,sr = librosa.load('../out/recording.wav',sr=None)
    df = Drumifier()
    df.setAudioLoopdata(y,sr)

    features = df.extractAudioFeatures()
    print("--------- FEATURES ----------")
    pp(features)

    tapSeq = df.makeTapSequenceFromAudioFeatures()
    print("--------- TAP_SEQUENCE ----------")
    pp(tapSeq)
    tsa = seq2audio(tapSeq,RATE)
    librosa.output.write_wav("../out/tapsequence.wav", tsa, sr)

    qtzTapSeq = df.quantizeTapSequence()
    print("--------- QUANTIZED_TAP_SEQUENCE ----------")
    pp(qtzTapSeq)
    qtsa = seq2audio(qtzTapSeq,RATE)
    librosa.output.write_wav("../out/quantized_tapsequence.wav", qtsa, sr)

    drumSeq = df.drumify()
    print("--------- DRUM_SEQUENCE ----------")
    pp(drumSeq)

    """instrument = 11
    drumSeq = df.changeInstrument(instrument)
    print("--------- CHANGE INSTRUMENT ----------")
    pp(drumSeq)"""

    drumAudio = df.drumSeq2audio("../soundfonts/aracno.sf2")
    print("--------- DRUM_AUDIO ----------")
    pp(drumAudio)
    librosa.output.write_wav("../out/drumified.wav", drumAudio, sr)

