"""360° version: the 3D-rendered letter (frames_prod, same camera as the set) over the rendered set,
with the shared virtual camera (dolly + orbit drift with depth parallax), typography and finishing
from comp.py."""
import os, sys, json, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comp as C

PD = os.environ.get('PROD_DIR', '../m3d/frames_prod')
TL = json.load(open(os.environ.get('TIMELINE', '../m3d/timeline.json')))
OD = os.environ.get('OUT_DIR', 'frames360')
W, H = C.W, C.H


def product(k):
    p = cv2.imread(f'{PD}/{k:04d}.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535.0
    if p.shape[:2] != (H, W):
        a = p[..., 3:4]
        pm = np.dstack([p[..., :3] * a, a])                 # resample premultiplied
        pm = cv2.resize(pm, (W, H), interpolation=cv2.INTER_CUBIC)
        a = np.clip(pm[..., 3:4], 0, 1)
        rgb = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0)
        p = np.dstack([np.clip(rgb, 0, 1), a])
    rgb = C.srgb2lin(p[..., :3][..., ::-1].copy())
    rgb = rgb * np.array([1.015, 1.0, 0.975], np.float32)  # same warm match as the photo version
    return rgb, p[..., 3]


def frame(k):
    t = k / C.FPS
    Z, Cx, Cy = C.smooth_keys(TL['cam'], t)
    pan = C.smooth_keys(TL['pan'], t)[0]
    bg = C.warp_bg(14, Z, np.array([Cx, Cy]), pan)
    rgb, a = product(k)
    a3 = a[..., None]
    wrap = cv2.GaussianBlur(bg, (0, 0), 6) * (cv2.GaussianBlur(1 - a, (0, 0), 3) * a)[..., None] * 0.12
    out = rgb * a3 + wrap + bg * (1 - a3)
    return C.finish(out, t, k)


def main(lo, hi):
    os.makedirs(OD, exist_ok=True)
    for k in range(lo, hi):
        fn = f'{OD}/{k:04d}.png'
        if os.path.exists(fn) or not os.path.exists(f'{PD}/{k:04d}.png'):
            continue
        t0 = time.time()
        out = frame(k)
        cv2.imwrite(fn, (out[..., ::-1] * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])
        print(k, round(time.time() - t0, 2), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        for k in map(int, sys.argv[2:]):
            cv2.imwrite(f'test360_{k:04d}.jpg', (frame(k)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        main(int(sys.argv[1]), int(sys.argv[2]))
