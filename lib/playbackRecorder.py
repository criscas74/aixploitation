from pprint import pprint as pp
import time
import pyaudio
import numpy as np
import librosa

CHUNK = 512  # CHUNKS of bytes to read each time from mic
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

class Recorder(object):
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.fulldata = np.array([])
        self.running = False
        self.startTime = self.stopTime = self.duration = 0

        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self.callback
        )

    def callback(self, in_data, frame_count, time_info, status):
        audio_data = np.fromstring(in_data, dtype=np.float32)
        if self.running:
            self.fulldata = np.append(self.fulldata, audio_data)
        return (audio_data, pyaudio.paContinue)

    def start(self):
        print("Started")
        self.fulldata = np.array([])
        self.running = True
        self.startTime = time.time()

    def stop(self):
        print("Stopped")
        self.running = False
        self.stopTime = time.time()
        self.duration = self.stopTime - self.startTime
        ret = {"data":self.fulldata.astype('float32'),"started":self.startTime,"stopped":self.stopTime,"duration":self.duration}
        return ret

    def save(self,filename,data=None):
        if data is None:
            data = self.fulldata
        librosa.output.write_wav(filename, data, RATE)

    def close(self):
        print("Closing all streams")
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate
        print("Bye!")


class Player():
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.rate = RATE
        self.fulldata = np.array([])
        self.buffpos = 0
        self.running = False
        self.startTime = self.stopTime = self.duration = 0

        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            frames_per_buffer=CHUNK,
            start=False,
            stream_callback = self.callback
        )

    def callback(self,in_data, frame_count, time_info, status):
        newBuf = self.buffpos + CHUNK
        audio_data = self.fulldata[self.buffpos:newBuf]
        self.buffpos = newBuf
        return (audio_data, pyaudio.paContinue)

    def start(self,inData=None):
        self.stream.stop_stream()
        self.buffpos = 0
        if inData is not None:
            self.fulldata = inData
            self.running = True
            self.startTime = time.time()
        print(type(self.fulldata))
        pp(self.fulldata)
        self.stream.start_stream()

    def is_active(self):
        return self.stream.is_active()

    def close(self):
        print("Closing all streams")
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate
        print("Bye!")

    def load(self,filename,sampleRate=RATE):
        print("Loading")
        y, sr = librosa.load(filename,sampleRate)
        self.fulldata = y
        self.rate = sr
        print("Loaded")

if __name__ == "__main__":

    filename = "../out/recording.wav"
    recording = {"data":[]}

    #"""
    recorder = Recorder()
    print("Rec Starting in 3secs")
    time.sleep(3)
    recorder.start()
    time.sleep(3)
    recording = recorder.stop()
    pp(recording)
    pp(type(recording['data']))
    time.sleep(1)
    print("saving %s"%filename)
    recorder.save(filename)
    recorder.close()
    #"""
    playFromFile = False
    #playFromFile = True
    player = Player()
    if playFromFile:
        player.load(filename)
        player.start()
    else:
        plData = recording['data']
        player.start(plData)

    loops =3
    for i in range(loops):
        print("%s loop of %s"%(i,loops))
        while player.is_active():
            pass
        else:
            player.start()

    player.close()

