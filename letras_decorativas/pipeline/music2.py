"""Original underscore for the spot (D major, 4/4, ~96 bpm): soft felt-like piano arpeggios,
a sparse piano melody, warm string pad and harp touches at the start and the end."""
import mido, random
random.seed(21)
TPB = 480; E8 = TPB // 2; BAR = TPB * 4
NOTES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def n(s): return 12 * (int(s[-1]) + 1) + NOTES[s[:-1]]

# bass, arpeggio voicing (8 eighths per bar)
bars = [
    ('D2', ['A3', 'D4', 'E4', 'F#4', 'A4', 'F#4', 'E4', 'D4']),     # Dadd9
    ('B1', ['F#3', 'B3', 'D4', 'F#4', 'A4', 'F#4', 'D4', 'B3']),    # Bm7
    ('G1', ['D3', 'G3', 'B3', 'D4', 'F#4', 'D4', 'B3', 'G3']),      # Gmaj7
    ('A1', ['E3', 'A3', 'D4', 'E4', 'G4', 'E4', 'D4', 'A3']),       # A7sus4
    ('F#2', ['D3', 'A3', 'D4', 'F#4', 'A4', 'F#4', 'D4', 'A3']),    # D/F#
    ('G2', ['D3', 'G3', 'B3', 'E4', 'F#4', 'E4', 'B3', 'G3']),      # Gmaj7(6)
    ('A2', ['E3', 'A3', 'C#4', 'E4', 'G4', 'E4', 'C#4', 'A3']),     # A7
]
mel = [  # (bar, eighth, length in eighths, note, vel)
    (1, 4, 2, 'F#5', 48), (1, 6, 2, 'A5', 50),
    (2, 0, 6, 'F#5', 52), (2, 6, 2, 'E5', 46),
    (3, 0, 4, 'D5', 50), (3, 4, 2, 'E5', 48), (3, 6, 2, 'F#5', 48),
    (4, 0, 6, 'E5', 50), (4, 6, 2, 'A4', 44),
    (5, 0, 4, 'B4', 46), (5, 4, 2, 'D5', 46), (5, 6, 2, 'E5', 46),
    (6, 0, 6, 'C#5', 44), (6, 6, 2, 'E5', 42),
]
pads = {1: ['F#3', 'B3', 'D4'], 2: ['G3', 'B3', 'D4'], 3: ['G3', 'A3', 'D4'], 4: ['F#3', 'A3', 'D4'],
        5: ['G3', 'B3', 'E4'], 6: ['G3', 'C#4', 'E4'], 7: ['F#3', 'A3', 'D4']}
ev = {k: [] for k in ('pno', 'str', 'harp', 'bass')}
def add(tr, t, dur, note, vel, jitter=10):
    t = max(0, int(t + random.gauss(0, jitter))); vel = max(1, min(127, int(vel + random.gauss(0, 3))))
    ev[tr].append((t, 1, note, vel)); ev[tr].append((t + int(dur), 0, note, 0))

for bi, (bass, arp) in enumerate(bars):
    t0 = bi * BAR
    add('pno', t0, BAR * 1.0, n(bass), 52)
    add('pno', t0, BAR * 1.0, n(bass) + 12, 34)
    for k, nn in enumerate(arp):
        v = 40 + (6 if k in (0, 4) else 0) + (4 if bi in (2, 3, 4) else 0)
        add('pno', t0 + k * E8, E8 * 3.2, n(nn), v)
# final chord (bar 8): rolled D major 9, ringing
t0 = 7 * BAR
for k, nn in enumerate(['D2', 'A2', 'D3', 'F#3', 'A3', 'E4', 'F#4', 'A4', 'D5']):
    add('pno', t0 + k * 45, BAR * 2.2, n(nn), 50 - k * 2, jitter=0)
for bar, pos, ln, note, vel in mel:
    add('pno', bar * BAR + pos * E8, ln * E8 * 1.1, n(note), vel + 6)
for bar, vs in pads.items():
    for nn in vs:
        add('str', bar * BAR, BAR * (2.2 if bar == 7 else 1.02), n(nn), 50 if bar < 7 else 44, jitter=0)
add('str', 7 * BAR, BAR * 2.2, n('D3'), 44, jitter=0)
for k, nn in enumerate(['D4', 'F#4', 'A4', 'D5', 'E5', 'F#5', 'A5']):
    add('harp', 30 + k * 70, BAR * 1.5, n(nn), 38 + k * 2, jitter=0)
for k, nn in enumerate(['A4', 'D5', 'F#5', 'A5', 'D6']):
    add('harp', 7 * BAR + 240 + k * 90, BAR * 1.6, n(nn), 40 + k * 2, jitter=0)

mid = mido.MidiFile(ticks_per_beat=TPB)
meta = mido.MidiTrack(); mid.tracks.append(meta)
tempo_map = [(0, 96), (6 * BAR, 90), (6 * BAR + TPB * 2, 84), (7 * BAR, 78)]
last = 0
for t, bpm in tempo_map:
    meta.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=t - last)); last = t
setup = {'pno': (0, 0, 60, 60, 96, 100), 'str': (49, 1, 70, 110, 66, 90), 'harp': (46, 2, 76, 100, 62, 100), 'bass': (0, 3, 64, 60, 80, 100)}
for name, (prog, ch, pan, rev, vol, expr) in setup.items():
    tr = mido.MidiTrack(); mid.tracks.append(tr)
    tr.append(mido.Message('program_change', program=prog, channel=ch, time=0))
    for cc, val in ((10, pan), (91, rev), (7, vol), (11, expr), (93, 10)):
        tr.append(mido.Message('control_change', control=cc, value=val, channel=ch, time=0))
    if name == 'pno':  # sustain pedal changes per bar
        pass
    evs = sorted(ev[name], key=lambda e: (e[0], e[1])); last = 0
    for t, on, note, vel in evs:
        tr.append(mido.Message('note_on' if on else 'note_off', note=note, velocity=vel, channel=ch, time=t - last)); last = t
mid.save('music.mid'); print('length s', round(mid.length, 2))
