"""Turntable angle per frame + virtual camera keys shared by the 3D render and the compositor."""
import numpy as np, json
FPS, DUR = 30, 20.0
N = int(FPS * DUR)
t = np.arange(N) / FPS
def ss(u): u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)
# angular speed: ease in (0.6-2.4 s), cruise, ease out (14.8-17.6 s) to a slow 2.5 deg/s drift
W_END = 2.5
shape = ss((t - 0.6) / 1.8) * (1 - ss((t - 14.8) / 2.8))
tail = ss((t - 14.8) / 2.8) * W_END
def total(wmax):
    w = wmax * shape + tail
    return np.concatenate([[0], np.cumsum(w[:-1]) / FPS])
TARGET, T_AT = 515.0, 17.6             # end on the floral side, three-quarter view showing the shoes
lo, hi = 1.0, 200.0
for _ in range(60):
    mid = (lo + hi) / 2
    if total(mid)[int(T_AT * FPS)] < TARGET: lo = mid
    else: hi = mid
phi = total(lo)
CAM = [(0.0, 1.08, 540, 1010), (2.5, 1.12, 540, 1030), (4.6, 1.32, 520, 1085), (6.6, 1.30, 555, 1095),
       (8.8, 1.12, 540, 1040), (11.5, 1.18, 545, 1050), (14.0, 1.06, 560, 985), (20.0, 1.10, 560, 990)]
PAN = [(0.0, 60.0), (20.0, -60.0)]
json.dump(dict(fps=FPS, phi=[round(float(p), 4) for p in phi], cam=CAM, pan=PAN), open('timeline.json', 'w'))
print('peak speed deg/s', round(lo, 1), '| phi at 2.5/4/6.5/9/11.5/14/17.6/20 s:',
      [round(float(phi[int(s * FPS) - 1]), 0) for s in (2.5, 4, 6.5, 9, 11.5, 14, 17.6, 20)])
