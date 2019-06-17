from pprint import pprint as pp
import sys

import numpy as np
import librosa
import librosa.display
import matplotlib
import matplotlib.pyplot as plt

try:
    filename = sys.argv[1]
except:
    filename = "test.wav"

print("reading: %s"%filename)

y, sr = librosa.load(filename)
onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
librosa.frames_to_time(onset_frames, sr=sr)
onset_env = librosa.onset.onset_strength(y, sr=sr)
onset_times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr)
onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)

tempo = librosa.beat.tempo(onset_envelope=onset_env, max_tempo=180)[0]
pp(librosa.beat.tempo(onset_envelope=onset_env, max_tempo=180))

"""
onset_env = librosa.onset.onset_strength(y, sr=sr)
tempo = librosa.beat.tempo(onset_envelope=onset_env, max_tempo=180)[0]
onset_times = librosa.onset.onset_detect(y, sr, units='time')
onset_frames = librosa.onset.onset_detect(y, sr, units='frames')
onset_strengths = librosa.onset.onset_strength(y, sr)[onset_frames]
normalized_onset_strengths = onset_strengths / np.max(onset_strengths)
onset_velocities = np.int32(normalized_onset_strengths * 127)
"""

D = np.abs(librosa.stft(y))
plt.figure()
ax1 = plt.subplot(2, 1, 1)
librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max), x_axis='time', y_axis='log')
plt.title('Power spectrogram')
plt.subplot(2, 1, 2, sharex=ax1)
plt.plot(onset_times, onset_env, label='Onset strength')
plt.vlines(onset_times[onset_frames], 0, onset_env.max(), color='r', alpha=0.9, linestyle='--', label='Onsets')
plt.axis('tight')
plt.legend(frameon=True, framealpha=0.75)

plt.show()