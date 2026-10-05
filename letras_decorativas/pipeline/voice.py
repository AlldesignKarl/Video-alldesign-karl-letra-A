"""Spanish (Spain) voice-over: Kokoro-82M, voice ef_dora, one phrase at a time with natural pauses,
then gentle broadcast processing (high-pass, warmth, presence, compression, small room)."""
import numpy as np, soundfile as sf, json
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve
from kokoro_onnx import Kokoro
T = '../tts/'
k = Kokoro(T + 'kokoro.onnx', T + 'voices.npz')
lines = json.load(open('lines.json'))
speeds = [1.0, 1.0, 0.97, 0.92]
SR = 48000; DUR = 20.0
start = 0.32
gaps = [0.32, 1.15, 0.55]
out = np.zeros(int(SR * DUR)); t = start; times = []
for i, l in enumerate(lines):
    if isinstance(l, dict):   # brand name: explicit phonemes (Spanish reading of an English name)
        a, sr = k.create(l['ph'], voice='ef_dora', speed=speeds[i], is_phonemes=True)
    else:
        a, sr = k.create(l, voice='ef_dora', speed=speeds[i], lang='es')
    e = np.where(np.abs(a) > 0.006)[0]; a = a[max(0, e[0] - 1200):e[-1] + 1600]
    a = resample_poly(a, SR, sr)
    n = len(a); fade = int(0.012 * SR); a[:fade] *= np.linspace(0, 1, fade); a[-fade * 4:] *= np.linspace(1, 0, fade * 4)
    s = int(t * SR); out[s:s + n] += a
    times.append([round(t, 3), round(t + n / SR, 3)])
    t += n / SR + (gaps[i] if i < len(gaps) else 0)
print('voice segments', times)
json.dump(times, open('voice_times.json', 'w'))
x = out
x = sosfilt(butter(2, 85, 'hp', fs=SR, output='sos'), x)
# low-mid warmth (+1.5 dB around 220 Hz) and presence (+2 dB around 4 kHz) via parallel band-pass
def band(x, lo, hi, g_db):
    return x + (10 ** (g_db / 20) - 1) * sosfilt(butter(2, [lo, hi], 'bp', fs=SR, output='sos'), x)
x = band(x, 150, 320, 1.5)
x = band(x, 2800, 5500, 2.0)
x = band(x, 6500, 9500, -1.5)   # tame sibilance
# compressor (RMS, 3:1 above -20 dBFS, smooth)
from scipy.ndimage import uniform_filter1d
x /= np.abs(x).max() + 1e-9; x *= 0.7
rms = np.sqrt(uniform_filter1d(x * x, int(0.01 * SR), origin=int(0.0049 * SR)) + 1e-12)
db = 20 * np.log10(rms); thr = -20; ratio = 3.0
gr = np.where(db > thr, (db - thr) * (1 - 1 / ratio), 0)
# causal attack/release smoothing (no look-ahead, so soft word onsets like the "m" keep their level)
aa, ar = np.exp(-1 / (0.003 * SR)), np.exp(-1 / (0.100 * SR))
g = np.empty_like(gr); acc = 0.0
for i, v in enumerate(gr):
    c = aa if v > acc else ar
    acc = c * acc + (1 - c) * v; g[i] = acc
x *= 10 ** (-g / 20)
# very small, warm room (synthetic IR, ~0.35 s decay), 9 % wet
rng = np.random.default_rng(3)
L = int(0.45 * SR); tt = np.arange(L) / SR
ir = rng.normal(0, 1, L) * np.exp(-tt / 0.09)
ir = sosfilt(butter(2, 5000, 'lp', fs=SR, output='sos'), ir); ir[: int(0.008 * SR)] = 0
ir /= np.sqrt((ir ** 2).sum())
wet = fftconvolve(x, ir)[: len(x)]
x = x + 0.09 * wet * (np.abs(x).max() / (np.abs(wet).max() + 1e-9))
sf.write('voice_proc.wav', x.astype(np.float32), SR)
print('done')
