"""Retiming v2: slow continuous turn of the decorated face only (165° -> 215°),
from almost frontal to a 3/4 view revealing the satin ballet shoes and ribbon."""
import numpy as np, json
from scipy.interpolate import PchipInterpolator
theta = np.load('theta.npy'); N = len(theta); fr = np.arange(1, N + 1, dtype=float)
FPS, DUR = 30, 20.5
NF = int(round(DUR * FPS)); t = np.arange(NF) / FPS
ss = lambda x: x * x * (3 - 2 * x)
v = 0.30 + 0.70 * ss(np.clip(t / 3.0, 0, 1))              # gentle start
v = v * (1 - 0.25 * ss(np.clip((t - 16.0) / 4.5, 0, 1)))   # settle a little at the end, still turning
cum = np.concatenate([[0], np.cumsum(v[1:] + v[:-1]) / 2]); cum /= cum[-1]
TH0, TH1 = 172.0, 218.0
th_out = TH0 + (TH1 - TH0) * cum
inv = PchipInterpolator(theta + np.arange(N) * 1e-6, fr)
src = inv(th_out)
json.dump(src.tolist(), open('timemap_v2.json', 'w'))
print('deg/s full speed', round((TH1 - TH0) / (cum[-1] and (np.sum(v) / FPS)) * 1, 2))
print('src range', round(src[0], 2), round(src[-1], 2), 'src per out frame min/max', round(np.diff(src).min(), 3), round(np.diff(src).max(), 3))
