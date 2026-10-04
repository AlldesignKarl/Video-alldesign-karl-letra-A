import soundfile as sf, numpy as np, json
from scipy.signal import resample_poly
SR = 48000; DUR = 20.5
starts = [0.45]
gaps = [0.35, 0.35, 0.25, 0.25, 0.35]
segs = []
for i in range(6):
    a, sr = sf.read(f'tts/v_ef_dora_{i}.wav')
    a = resample_poly(a, SR, sr)
    segs.append(a)
t = starts[0]; times = []
out = np.zeros(int(SR * DUR))
for i, a in enumerate(segs):
    s = int(t * SR); out[s:s + len(a)] += a
    times.append((round(t, 3), round(t + len(a) / SR, 3)))
    t += len(a) / SR + (gaps[i] if i < 5 else 0)
print(times)
json.dump(times, open('voice_times.json', 'w'))
sf.write('voice_dry.wav', out.astype(np.float32), SR)
