"""Multi-frame fusion: align neighbouring source frames to frame i with dense optical flow
and blend them with photometric weights -> removes WhatsApp compression noise/blocking."""
import cv2, numpy as np
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
dis.setFinestScale(0)

def load(i):
    return cv2.imread(f'full/{i:04d}.png').astype(np.float32) / 255

def fuse(i, x0, y0, x1, y1, R=3, sigma=0.035, N=394):
    ref = load(i)
    pad = 24
    X0, Y0 = max(0, x0 - pad), max(0, y0 - pad)
    X1, Y1 = min(ref.shape[1], x1 + pad), min(ref.shape[0], y1 + pad)
    r = ref[Y0:Y1, X0:X1]
    # work at 2x for sub-pixel accurate alignment
    up = lambda im: cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    rU = up(r); gR = cv2.cvtColor((np.clip(rU, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    acc = rU.copy(); wsum = np.ones(rU.shape[:2], np.float32)
    h, w = rU.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    for j in range(i - R, i + R + 1):
        if j == i or j < 1 or j > N: continue
        o = up(load(j)[Y0:Y1, X0:X1])
        gO = cv2.cvtColor((np.clip(o, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        fl = dis.calc(gR, gO, None)
        wo = cv2.remap(o, gx + fl[..., 0], gy + fl[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        d = cv2.GaussianBlur(((wo - rU) ** 2).sum(-1), (0, 0), 2.0)
        wt = np.exp(-d / (2 * sigma ** 2)) * (0.85 ** abs(j - i))
        acc += wo * wt[..., None]; wsum += wt
    f = acc / wsum[..., None]
    f = cv2.resize(f, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_AREA)
    out = ref.copy(); out[Y0:Y1, X0:X1] = f
    return out
