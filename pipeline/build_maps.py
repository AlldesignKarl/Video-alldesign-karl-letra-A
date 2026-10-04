"""Rotation angle per source frame -> stabilisation transforms (xforms.json) and the
output->source retiming map (timemap.json) for a smooth, slow, continuous turn."""
import numpy as np, json, sys
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.interpolate import PchipInterpolator, UnivariateSpline

rows = np.load('rot_rows.npy')          # y0, y1, xl, xr, axis, fw
N = len(rows)
S = np.load('vscale.npy')[:N]            # camera zoom relative to frame 1 (vertical flow)
S = gaussian_filter1d(S, 1.0)
coefs = np.load('vcoefs.npy')
fr = np.arange(1, N + 1, dtype=float)
fw = median_filter(rows[:, 5] / S, 5)
fw = gaussian_filter1d(fw, 1.5)

# --- branch-wise inversion of fw(θ) = fw_max * cos(θ - θ_branch)
D = float(np.min(fw))                     # side-view thickness
# local minima = side views (θ = 90, 270)
mins = [i for i in range(5, N - 5) if fw[i] == fw[max(0, i - 25):i + 26].min() and fw[i] < 0.6 * fw.max()]
# collapse neighbours
mm = []
for i in mins:
    if not mm or i - mm[-1] > 30: mm.append(i)
mins = mm
print('side views at frames', [m + 1 for m in mins], 'fw', [round(fw[m], 1) for m in mins])

pts = []                                  # (frame, theta_deg)
seg_bounds = [0] + mins + [N - 1]
quarter = 90.0
for si, m in enumerate(mins):
    th_side = 90.0 + 180.0 * si
    # local fw_max around this side view (frontal-ish maxima on each side)
    # split at the frontal maxima between consecutive side views
    lo = (mins[si - 1] + int(np.argmax(fw[mins[si - 1]:m + 1]))) if si > 0 else 0
    hi = (m + int(np.argmax(fw[m:mins[si + 1] + 1]))) if si + 1 < len(mins) else N - 1
    left = fw[lo:m + 1]; right = fw[m:hi + 1]
    fmL = left.max(); fmR = right.max()
    Dm = fw[m]
    # descending branch (before side view): θ = th_side - acos((fw - ...)) using model
    for i in range(lo, m + 1):
        r = fw[i]
        WL = np.sqrt(max(fmL ** 2 - Dm ** 2, 1))
        # solve W cos(φ) + D sin(φ) = r for φ = angle from frontal in [θm, 90]
        thm = np.degrees(np.arctan2(Dm, WL)); R = np.hypot(WL, Dm)
        if r / R < 0.97 and r >= Dm * 1.35:
            phi = thm + np.degrees(np.arccos(np.clip(r / R, -1, 1)))
            pts.append((i + 1, th_side - 90 + min(phi, 90.0)))
    for i in range(m, hi + 1):
        r = fw[i]
        WR = np.sqrt(max(fmR ** 2 - Dm ** 2, 1))
        thm = np.degrees(np.arctan2(Dm, WR)); R = np.hypot(WR, Dm)
        if r / R < 0.97 and r >= Dm * 1.35:
            phi = thm + np.degrees(np.arccos(np.clip(r / R, -1, 1)))
            pts.append((i + 1, th_side + 90 - min(phi, 90.0)))
pts = np.array(sorted(pts))
# robust monotone fit: bin medians -> PCHIP, linear extension at the ends
bins = np.arange(1, N + 16, 15)
bc, bt = [], []
for lo_, hi_ in zip(bins[:-1], bins[1:]):
    sel = (pts[:, 0] >= lo_) & (pts[:, 0] < hi_)
    if sel.sum() >= 4:
        bc.append(np.median(pts[sel, 0])); bt.append(np.median(pts[sel, 1]))
bc, bt = np.array(bc), np.maximum.accumulate(np.array(bt))
# guarantee strictly increasing
bt = bt + np.arange(len(bt)) * 1e-3
pc = PchipInterpolator(bc, bt, extrapolate=False)
theta = pc(fr)
s0 = (bt[1] - bt[0]) / (bc[1] - bc[0]); s1 = (bt[-1] - bt[-2]) / (bc[-1] - bc[-2])
theta = np.where(fr < bc[0], bt[0] + (fr - bc[0]) * s0, theta)
theta = np.where(fr > bc[-1], bt[-1] + (fr - bc[-1]) * s1, theta)
P = 40
sl0 = (theta[10] - theta[0]) / 10; sl1 = (theta[-1] - theta[-11]) / 10
ext = np.concatenate([theta[0] + sl0 * np.arange(-P, 0), theta, theta[-1] + sl1 * np.arange(1, P + 1)])
theta = gaussian_filter1d(ext, 10.0)[P:-P]
theta = np.maximum.accumulate(theta)
vel = np.gradient(theta)
print('theta range', round(theta[0], 1), round(theta[-1], 1))
for i in range(0, N, 20):
    print(i + 1, round(theta[i], 1), 'vel deg/s', round(vel[i] * 30, 1), 'fw', round(fw[i], 1))
np.save('theta.npy', theta)

# --- stabilisation: axis x = footprint bbox centre; base-centre y from lowest point minus
#     the perspective drop of the nearest footprint corner, Δy = (W/2|sinθ| + D/2|cosθ|)·sin(elev)
W0 = float(np.sqrt(max(fw.max() ** 2 - D ** 2, 1)))
elev = np.radians(17.0)
tr = np.radians(theta)
dy = (W0 / 2 * np.abs(np.sin(tr)) + D / 2 * np.abs(np.cos(tr))) * np.sin(elev)   # in frame-1 px units
axis = gaussian_filter1d(rows[:, 4], 2.0)
ym = rows[:, 1] - dy * S                   # mask-based base-centre estimate
# flow-integrated trajectory of the same 3D point (complementary filter)
yf = np.zeros(N); yf[0] = ym[0]
for i in range(N - 1):
    a_, b_, m_ = coefs[i]
    yf[i + 1] = yf[i] + a_ * (yf[i] - m_) + b_
basey = yf + gaussian_filter1d(ym - yf, 45.0)
print('base y: mask vs fused (every 30)', [(int(ym[i]), int(basey[i])) for i in range(0, N, 30)])
# letter height for scale: top of body (y0) is affected by the shoes later on; use a robust
# global scale with gentle trend instead
hgt = (basey - rows[:, 0]) / S
print('height/S stats', np.percentile(hgt, [5, 50, 95]))
a0 = 290.0 / np.median(hgt[:40])          # nominal canonical letter height 290 px (frontal frames)
CW, CH, AX, AY = 420, 440, 210, 370
xf = []
for i in range(N):
    a = a0 / S[i]
    xf.append(dict(a=float(a), bx=float(AX - a * axis[i]), by=float(AY - a * basey[i])))
json.dump(xf, open('xforms.json', 'w'))
json.dump(dict(screen_scale=1.0, a0=float(a0)), open('xforms_meta.json', 'w'))

# --- output retiming: slow continuous turn. Ease-in at the start, gentle slow-down at the end so the
#     decorated (floral) face is frontal during the closing line, still turning.
FPS, DUR = 30, 20.5
NF = int(round(DUR * FPS))
t = np.arange(NF) / FPS
r = np.clip(t / 2.6, 0, 1); v = 0.22 + 0.78 * r * r * (3 - 2 * r)
r2 = np.clip((t - 15.5) / 5.0, 0, 1); v = v * (1 - 0.35 * r2 * r2 * (3 - 2 * r2))
cum = np.concatenate([[0], np.cumsum(v[1:] + v[:-1]) / 2]) / FPS
th0 = theta[0]
T_FRONT, TH_FRONT = float(sys.argv[1]) if len(sys.argv) > 1 else 18.6, float(sys.argv[2]) if len(sys.argv) > 2 else 182.0
k = int(round(T_FRONT * FPS))
omega = (TH_FRONT - th0) / cum[k]
th_out = th0 + omega * cum
print('omega (deg/s at full speed)', round(omega, 2), 'end angle', round(th_out[-1], 1))
inv = PchipInterpolator(theta + np.arange(N) * 1e-6, fr)
src = np.clip(inv(np.minimum(th_out, theta[-1])), 1, N)
json.dump(src.tolist(), open('timemap.json', 'w'))
print('src idx every 2s', [round(float(s), 1) for s in src[::60]], 'last', round(float(src[-1]), 1))
