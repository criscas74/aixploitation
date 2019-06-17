import pyaudio

p = pyaudio.PyAudio()

CHUNK = 1024
#FORMAT = pyaudio.paInt16
FORMAT = pyaudio.paFloat32

CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 2

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=512)

while True:
    data = stream.read(512)

"""
for CHUNK1 in [512,2048,4096,8192,16384]:
    for CHUNK2 in [512,2048,4096,8192,16384]:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK1)


        try:
            print CHUNK1,CHUNK2
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK2)
        except:
            print "Boohoo"

        stream.stop_stream()
        stream.close()

"""