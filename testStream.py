import mido
import time
import pyaudio
import copy
import numpy as np
import librosa


CHUNK = 512  # CHUNKS of bytes to read each time from mic
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100


fulldata = np.array([])
recording = False

def callback(in_data, frame_count, time_info, status):
    global fulldata,recording
    audio_data = np.fromstring(in_data, dtype=np.float32)
    if recording:
        fulldata = np.append(fulldata, audio_data)
    return (audio_data, pyaudio.paContinue)

p = pyaudio.PyAudio()


stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                frames_per_buffer=CHUNK,

                input=True,
                output=True,
                start=True,
                stream_callback=callback)

while True:
    recording = True