from pprint import pprint as pp
import time

from collections import deque
import mido

inport_name = 'MIDI4x4 Midi In 1'

inport = mido.open_input(inport_name)

qpm = None

tap_qpm_samples = 4
queue = deque(maxlen=tap_qpm_samples)

def get_qpm(now,last_time):
    if last_time != 0:
        time_diff = now - last_time
        queue.append(time_diff)
        if len(queue) >= tap_qpm_samples:
            return (60 / (sum(queue) / len(queue) ) )

last_time = 0
while 1:
    for message in inport:
        if message.type == 'note_on':
            pp(message)
            now = time.time()
            if now - last_time > 0.3: #debounce
                qpm = get_qpm(now,last_time)
                print(qpm)
                print(queue)
            last_time = now

        if qpm is not None:
            print("QPM: %s"%qpm)
            queue = deque(maxlen=tap_qpm_samples)
