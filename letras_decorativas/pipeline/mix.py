import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt
from scipy.ndimage import uniform_filter1d, minimum_filter1d
SR = 48000; DUR = 20.0; N = int(SR * DUR)
v, sr = sf.read('voice_proc.wav'); v = np.pad(v[:N], (0, max(0, N - len(v))))
m, sr = sf.read('music_raw.wav'); m = m[:N]; m = np.pad(m, ((0, N - len(m)), (0, 0)))
meter = pyln.Meter(SR)
m = sosfilt(butter(2, 60, 'hp', fs=SR, output='sos'), m, axis=0)
m = sosfilt(butter(1, 10000, 'lp', fs=SR, output='sos'), m, axis=0)
v *= 10 ** ((-16.0 - meter.integrated_loudness(v)) / 20)
m *= 10 ** ((-24.5 - meter.integrated_loudness(m)) / 20)
# ducking under the voice (~5 dB), and an extra 2.5 dB dip for the final store line
env = uniform_filter1d(np.abs(v), int(0.05 * SR))
act = uniform_filter1d((env > 0.01).astype(float), int(0.35 * SR)); act = np.clip(act * 1.6, 0, 1)
t = np.arange(N) / SR
extra = np.clip((t - 15.6) / 0.8, 0, 1) * 2.5
duck = 10 ** ((-5.0 * act - extra) / 20)
m *= duck[:, None]
fin = np.clip(t / 0.6, 0, 1) ** 1.5
fout = np.clip((DUR - t) / 1.3, 0, 1) ** 1.2
m *= (fin * fout)[:, None]
mix = np.stack([v, v], 1) + m
mix *= 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
lim = 10 ** (-1.2 / 20)
over = np.abs(mix).max(1) / lim
g = np.minimum(1, 1 / np.maximum(over, 1e-9))
g = uniform_filter1d(minimum_filter1d(g, int(0.004 * SR)), int(0.004 * SR))
mix *= g[:, None]
print('final LUFS', round(meter.integrated_loudness(mix), 2), 'peak dB', round(20 * np.log10(np.abs(mix).max()), 2))
sf.write('mix.wav', mix.astype(np.float32), SR, subtype='PCM_24')
sf.write('music_mixstem.wav', m.astype(np.float32), SR, subtype='PCM_24')
