import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt
SR = 48000; DUR = 20.5; N = int(SR * DUR)
v, sr = sf.read('voice_proc.wav'); assert sr == SR
v = v[:N] if v.ndim == 1 else v[:N].mean(1)
v = np.pad(v, (0, N - len(v)))
m, sr = sf.read('music_raw.wav'); assert sr == SR
m = m[:N]; m = np.pad(m, ((0, N - len(m)), (0, 0)))
meter = pyln.Meter(SR)
# music: gentle low cut + tame harsh highs
m = sosfilt(butter(2, 70, 'hp', fs=SR, output='sos'), m, axis=0)
m = sosfilt(butter(1, 9000, 'lp', fs=SR, output='sos'), m, axis=0)
# levels
v *= 10 ** ((-16.0 - meter.integrated_loudness(v)) / 20)
m *= 10 ** ((-23.5 - meter.integrated_loudness(m)) / 20)
# ducking envelope from voice activity (smooth, ~5 dB)
env = np.abs(v)
win = int(0.05 * SR)
from scipy.ndimage import uniform_filter1d
env = uniform_filter1d(env, win)
act = (env > 0.01).astype(float)
k = int(0.35 * SR); act = uniform_filter1d(act, k); act = np.clip(act * 1.6, 0, 1)
duck = 10 ** (-5.5 * act / 20)
m *= duck[:, None]
# fades
t = np.arange(N) / SR
fin = np.clip(t / 0.9, 0, 1) ** 1.5
fout = np.clip((DUR - t) / 1.6, 0, 1) ** 1.3
m *= (fin * fout)[:, None]
vo = np.stack([v, v], 1)
mix = vo + m
mix *= 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
# soft limiter to -1 dBTP-ish
peak = np.abs(mix).max(); lim = 10 ** (-1.2 / 20)
if peak > lim:
    g = np.ones(N)
    over = np.abs(mix).max(1) / lim
    g = np.minimum(1, 1 / np.maximum(over, 1e-9))
    # smooth gain (fast attack, slow release)
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    g = minimum_filter1d(g, int(0.004 * SR)); g = uniform_filter1d(g, int(0.004 * SR))
    mix *= g[:, None]
print('final LUFS', round(meter.integrated_loudness(mix), 2), 'peak dB', round(20 * np.log10(np.abs(mix).max()), 2))
sf.write('mix.wav', mix.astype(np.float32), SR, subtype='PCM_24')
