from pprint import  pprint as pp
from magenta.music.drums_encoder_decoder import DEFAULT_DRUM_TYPE_PITCHES

DRUM_PIECES = {
    0:"kick drum",
    1:"snare drum",
    2:"closed hi-hat",
    3:"open hi-hat",
    4:"low tom",
    5:"mid tom",
    6:"high tom",
    7:"crash cymbal",
    8:"ride cymbal",
}

drum_type_pitches = DEFAULT_DRUM_TYPE_PITCHES
drum_map = dict(enumerate(drum_type_pitches))
inverse_drum_map = dict((pitch, index)
                          for index, pitches in drum_map.items()
                          for pitch in pitches)

compact_inverse_map = dict((v[0],k) for k,v in drum_map.items())

inverse_drum_map = dict((k,DRUM_PIECES[v]) for k,v in inverse_drum_map.items())


tabla_set = set([36,38,42,46,47,50,52,53,59,60,62,64,65,65,67,69,71,72,74,76,77,79,81,83,84,88,89,91,93,95,96])

print(tabla_set.difference(inverse_drum_map.keys()))

print(set([inverse_drum_map[x] for x in set(inverse_drum_map.keys()).intersection(tabla_set)]))

print(set([inverse_drum_map[x] for x in set(inverse_drum_map.keys()).difference(tabla_set)]))