from pprint import pprint as pp
import mido

inport_name = 'MIDI4x4 Midi In 1'
throughport_name = 'MIDI4x4 Midi Out 1'

beatsPerLoop = 2

print("Opening midi connection")
inport = mido.open_input(inport_name)
throughport = mido.open_output(throughport_name)

for message in inport:
    if message.type != "clock":
        print("-"*100)
        print(message.type,message)
