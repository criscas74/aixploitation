import mido
import time
import pyaudio
import copy
import numpy as np
import librosa
from magenta import music as mm
from magenta.models.music_vae import configs
from magenta.models.music_vae.trained_model import TrainedModel
from magenta.music import midi_synth
from magenta.protobuf import music_pb2

from pprint import pprint as pp

"""
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print "Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')

import sys
sys.exit()
"""

CHUNK = 512  # CHUNKS of bytes to read each time from mic
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

TICKS_QUARTER = 96 // 4
TICKS_HALF = 96 // 2
TICKS_WHOLE = 96 // 1

p = pyaudio.PyAudio()

GROOVAE_2BAR_TAP_FIXED_VELOCITY = "groovae_2bar_tap_fixed_velocity.tar"
config_2bar_tap = configs.CONFIG_MAP['groovae_2bar_tap_fixed_velocity']
groovae_2bar_tap = TrainedModel(config_2bar_tap, 1, checkpoint_dir_or_path=GROOVAE_2BAR_TAP_FIXED_VELOCITY)

def drumify(s, model, temperature=1.0):
    encoding, mu, sigma = model.encode([s])
    decoded = model.decode(encoding, length=32, temperature=temperature)
    return decoded[0]

def make_tap_sequence(tempo, onset_times, onset_frames, onset_velocities,
                      velocity_threshold, start_time, end_time):
    #pp(locals())
    note_sequence = music_pb2.NoteSequence()
    note_sequence.tempos.add(qpm=tempo)
    #print("="*100)
    #print("Tempo: %s"%tempo)
    #print("="*100)
    for onset_vel, onset_time in zip(onset_velocities, onset_times):
        #print("vel: %s, time: %s" % (onset_vel, onset_time))
        if onset_vel > velocity_threshold and onset_time >= start_time and onset_time < end_time:  # filter quietest notes
            start = onset_time - start_time
            end = start + 0.01
            note_sequence.notes.add(
                instrument=9, pitch=42, is_drum=True,
                velocity=onset_vel,  # model will use fixed velocity here
                start_time=start,
                end_time=end
            )
            print("add - start: %s, end: %s, velocity: %s"%(start,end,onset_vel))
        else:
            print("discard")
            pass
        #print("-"*100)
    #print("="*100)
    #print("Note sequence")
    #print("="*100)
    #pp(note_sequence)
    #import sys; sys.exit(1)
    return note_sequence

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

fulldata = np.array([])
recording = False

def callback(in_data, frame_count, time_info, status):
    global fulldata,recording
    audio_data = np.fromstring(in_data, dtype=np.float32)
    if recording:
        fulldata = np.append(fulldata, audio_data)
    return (audio_data, pyaudio.paContinue)

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK,
                start=True,
                stream_callback=callback)

audio2send = []
cur_data = ''


inPort  = mido.open_input('USB MIDI Interface')
outPort = mido.open_output('magenta_clock', virtual=True)
cc = 1
metronome_signals  = (
  [mido.Message(type='control_change', control=cc, value=127)] +
  [mido.Message(type='control_change', control=cc, value=0)] * 3)
recording_bars_limit = 3

started = False
tick = 0
quarterTick = 0
prec_time = time.time()
rec_bar = 0
qpm = 0
tempo = 0

recStartTime = 0
recEndTime = 0

for message in inPort:
    if message.type == 'clock':
        tick += 1
        if tick % TICKS_QUARTER == 0:
            message = metronome_signals[quarterTick]
            #print("Message: %s" % message)
            print("QUARTER: %s - qpm: %s - tempo: %s - started: %s - recording bar: %s" % (
            quarterTick, qpm, tempo, started, rec_bar))
            outPort.send(message)
            quarterTick += 1
            if quarterTick % 4 == 0:
                quarterTick = 0
        if tick % TICKS_HALF == 0:
            now = time.time()
            tempo = (now - prec_time) * 1000000
            prec_time = now
            qpm = round(mido.tempo2bpm(tempo),1) * 2
            #print("qpm: %s, tempo: %s" % (qpm, tempo))
        if tick % TICKS_WHOLE == 0:
            rec_bar += 1
            if rec_bar % recording_bars_limit == 0:
                rec_bar = 0
    elif message.type == 'start':
        tick = 0
        rec_bar = 0
        quarterTick = 0
        started = True
        recStartTime = time.time()
    elif message.type == 'stop':
        started = False


    if started == True and recording == False:
        print("Started and this is the first tick: recording")
        recording = True
    elif recording == True and rec_bar == recording_bars_limit -1 and quarterTick == 0:
        print("Stopped recording")
        recording = False
        started = False
        recEndTime = time.time()
        pp(fulldata)
        print(type(fulldata))

        y = fulldata
        sr = RATE
        onset_times = librosa.onset.onset_detect(y, sr, units='time')
        onset_frames = librosa.onset.onset_detect(y, sr, units='frames')
        onset_strengths = librosa.onset.onset_strength(y, sr)[onset_frames]
        normalized_onset_strengths = onset_strengths / np.max(onset_strengths)
        onset_velocities = np.int32(normalized_onset_strengths * 127)

        cippa = "stocazzo"
        librosa.output.write_wav("seq_%s.wav" % cippa, fulldata, sr)

        velocity_threshold = 30

        initial_start_time = 0 # onset_times[0] #okkio io lo metterei a 0
        start_time = 0 # onset_times[0] #okkio io lo metterei a 0
        beat_length = 60 / qpm
        two_bar_length = beat_length * 8
        end_time = start_time + two_bar_length

        print("DURATION: Time based: {} - Actual: {}".format(end_time, recEndTime - recStartTime))

        s = make_tap_sequence(qpm,onset_times,onset_frames,onset_velocities,velocity_threshold,start_time,end_time)
        seq_to_save = librosa.util.normalize(midi_synth.fluidsynth(s, sample_rate=sr))
        librosa.output.write_wav("tapped_out.wav", seq_to_save, sr)

        temperature = 0.1
        h = drumify(s, groovae_2bar_tap, temperature=temperature)

        combined_drum_sequence = start_notes_at_0(combine_sequences_with_lengths([h], [end_time-start_time]))
        full_drum_audio = librosa.util.normalize(midi_synth.fluidsynth(combined_drum_sequence, sample_rate=sr))

        drums_and_original = mix_tracks(full_drum_audio, y[int(initial_start_time * sr):] / 2, stereo=True)

        librosa.output.write_wav("mixed_out.wav", drums_and_original, sr)
        librosa.output.write_wav("alone_out.wav", full_drum_audio, sr)

        fulldata = np.array([])
