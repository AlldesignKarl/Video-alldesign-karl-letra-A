"""Original 3/4 piece with a slow 'jota aragonesa' flavour: fingerpicked nylon guitar,
a simple guitar melody, warm string pad and a harp roll at the start and end."""
import mido, random
random.seed(11)
TPB = 480
E8 = TPB // 2
BAR = TPB * 3

# note helpers
NOTES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def n(s):
    name, octv = s[:-1], int(s[-1])
    return 12 * (octv + 1) + NOTES[name]

chords = [  # (bass, [mid1, mid2, top]) per bar -- p-i-m-a-m-i pattern
    ('A2', ['E3', 'A3', 'C#4']),   # 1 A
    ('A2', ['E3', 'A3', 'C#4']),   # 2 A
    ('E2', ['B2', 'G#3', 'D4']),   # 3 E7
    ('E2', ['B2', 'G#3', 'D4']),   # 4 E7
    ('A2', ['E3', 'A3', 'C#4']),   # 6 A
    ('D3', ['A3', 'D4', 'F#4']),   # 7 D
    ('C#3', ['E3', 'A3', 'C#4']),  # 8 A/C#
    ('B2', ['F#3', 'A3', 'D4']),   # 9 Bm7
    ('E2', ['B2', 'G#3', 'D4']),   # 10 E7
    ('A2', ['E3', 'A3', 'C#4']),   # 11 A
    ('A2', ['E3', 'A3', 'C#4']),   # 12 A (final)
]
# melody: list of (bar, beat_offset_in_eighths, length_in_eighths, note)
mel = []
def m(bar, pos, ln, note, vel=74):
    mel.append((bar, pos, ln, n(note), vel))
m(2, 4, 2, 'E4', 62)
m(3, 0, 4, 'D5'); m(3, 4, 1, 'C#5', 66); m(3, 5, 1, 'B4', 64)
m(4, 0, 2, 'G#4', 66); m(4, 2, 2, 'B4', 68); m(4, 4, 2, 'D5', 70)
m(5, 0, 6, 'C#5', 74)
m(6, 0, 2, 'D5', 70); m(6, 2, 2, 'F#5', 72); m(6, 4, 1, 'E5', 66); m(6, 5, 1, 'D5', 64)
m(7, 0, 6, 'C#5', 72)
m(8, 0, 2, 'B4', 66); m(8, 2, 2, 'D5', 68); m(8, 4, 1, 'C#5', 64); m(8, 5, 1, 'B4', 62)
m(9, 0, 4, 'B4', 66); m(9, 4, 2, 'G#4', 62)
m(10, 0, 6, 'A4', 66)

pads = {  # sustained string voicing per bar (from bar 3)
    3: ['E3', 'B3', 'G#4'], 4: ['E3', 'D4', 'G#4'], 5: ['A3', 'C#4', 'E4'],
    6: ['A3', 'D4', 'F#4'], 7: ['A3', 'C#4', 'E4'], 8: ['A3', 'D4', 'F#4'], 9: ['G#3', 'D4', 'E4'],
    10: ['A3', 'C#4', 'E4'], 11: ['A3', 'C#4', 'E4'],
}

events = {k: [] for k in ('gtr', 'mel', 'str', 'harp')}
def add(track, t, dur, note, vel):
    t = max(0, int(t + random.gauss(0, 8)))
    vel = max(1, min(127, int(vel + random.gauss(0, 4))))
    events[track].append((t, 1, note, vel))
    events[track].append((t + int(dur), 0, note, 0))

for bi, (bass, (m1, m2, top)) in enumerate(chords):
    t0 = bi * BAR
    final = bi == len(chords) - 1
    if final:
        # gentle rolled final chord, let it ring
        for k, nn in enumerate([bass, m1, m2, top, 'E4', 'A4']):
            add('gtr', t0 + k * 55, BAR * 2.2, n(nn), 66 - k * 2)
        continue
    pat = [bass, m1, m2, top, m2, m1]
    dyn = 1.0 if bi > 0 else 0.85
    for k, nn in enumerate(pat):
        vel = (70 if k == 0 else 56 if k == 3 else 48) * dyn
        # each plucked string rings until re-plucked
        dur = E8 * (6 - k) if k in (0,) else E8 * 2.6
        add('gtr', t0 + k * E8, dur, n(nn), vel)

for bar, pos, ln, note, vel in mel:
    t = (bar - 1) * BAR + pos * E8
    add('mel', t, ln * E8 * 1.05, note, vel)

for bar, vs in pads.items():
    t = (bar - 1) * BAR
    ln = BAR * (2.4 if bar == 11 else 1.0)
    for nn in vs:
        add('str', t, ln, n(nn), 62 if bar == 11 else 52)

# harp: rolled arpeggio at the start and a closing roll up
for k, nn in enumerate(['A3', 'C#4', 'E4', 'A4', 'C#5', 'E5']):
    add('harp', 0 + k * 70, BAR * 2, n(nn), 46 + k * 2)
for k, nn in enumerate(['A4', 'C#5', 'E5', 'A5', 'C#6', 'E6']):
    add('harp', 10 * BAR + E8 * 2 + k * 80, BAR * 1.6, n(nn), 56 + k * 2)

mid = mido.MidiFile(ticks_per_beat=TPB)
meta = mido.MidiTrack(); mid.tracks.append(meta)
meta.append(mido.MetaMessage('time_signature', numerator=3, denominator=4, time=0))
# tempo: q=104, gentle ritardando over the last two bars
tempo_map = [(0, 108), (9 * BAR, 102), (9 * BAR + TPB * 2, 96), (10 * BAR, 88), (10 * BAR + TPB, 80)]
last = 0
for t, bpm in tempo_map:
    meta.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=t - last)); last = t

setup = {  # program, channel, pan, reverb, volume, expression
    'gtr': (24, 0, 52, 70, 100, 110),
    'mel': (24, 1, 76, 78, 92, 112),
    'str': (49, 2, 64, 100, 70, 90),
    'harp': (46, 3, 70, 100, 70, 100),
}
for name, (prog, ch, pan, rev, vol, expr) in setup.items():
    tr = mido.MidiTrack(); mid.tracks.append(tr)
    tr.append(mido.Message('program_change', program=prog, channel=ch, time=0))
    for cc, val in ((10, pan), (91, rev), (7, vol), (11, expr), (93, 0)):
        tr.append(mido.Message('control_change', control=cc, value=val, channel=ch, time=0))
    ev = sorted(events[name], key=lambda e: (e[0], e[1]))
    last = 0
    for t, on, note, vel in ev:
        tr.append(mido.Message('note_on' if on else 'note_off', note=note, velocity=vel, channel=ch, time=t - last))
        last = t
mid.save('music.mid')
print('length s', mid.length)
