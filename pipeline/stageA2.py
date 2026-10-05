"""Stage A: per source frame -> super-resolved, stabilised, matted product sprite (RGBA).
Transforms come from xforms.json: for each frame, source->canonical mapping can = a*src + (bx, by).
Canonical LR canvas: CW x CH, rotation axis at (AX, AY) (base centre)."""
import sys, os, json, numpy as np, cv2, time, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtools, pymatting
torch.set_num_threads(int(os.environ.get('NT', '4')))

CW, CH, AX, AY = 420, 440, 210, 370
K = float(os.environ.get('SPRITE_K', '2.05'))   # sprite scale relative to canonical LR
SW, SH = int(round(CW * K)), int(round(CH * K))
xf = json.load(open('xforms.json'))
lo, hi = int(sys.argv[1]), int(sys.argv[2])
SD = os.environ.get('SPR_DIR', 'sprites'); LD = os.environ.get('LR_DIR', 'lr'); HD = os.environ.get('HR_DIR', 'hr')
os.makedirs(SD, exist_ok=True); os.makedirs(LD, exist_ok=True)


def box(img, r):
    return cv2.boxFilter(img, -1, (2 * r + 1, 2 * r + 1), normalize=True, borderType=cv2.BORDER_REFLECT)


def guided(I, p, r, eps):
    """Fast guided filter, I: HxWx3 guide (float), p: HxW."""
    mI = box(I, r); mp = box(p, r)
    cov = box(I * p[..., None], r) - mI * mp[..., None]
    var = np.zeros(I.shape[:2] + (3, 3), np.float32)
    for i in range(3):
        for j in range(3):
            var[..., i, j] = box(I[..., i] * I[..., j], r) - mI[..., i] * mI[..., j]
    var += eps * np.eye(3, dtype=np.float32)
    a = np.linalg.solve(var, cov[..., None])[..., 0]
    b = mp - (a * mI).sum(-1)
    return (box(a, r) * I).sum(-1) + box(b, r)


for i in range(lo, hi + 1):
    if os.path.exists(f'{SD}/{i:04d}.png'):
        continue
    t0 = time.time()
    a, bx, by = xf[i - 1]['a'], xf[i - 1]['bx'], xf[i - 1]['by']
    m = (cv2.imread(f'masks_fwd/{i:04d}.png', 0) > 127).astype(np.float32)
    hp = f'holes/{i:04d}.png' if os.path.exists(f'holes/{i:04d}.png') else f'holes_fwd/{i:04d}.png'
    if os.path.exists(hp):          # A's counter + leg gap (see-through regions)
        hm = (cv2.imread(hp, 0) > 127).astype(np.uint8)
        hm = cv2.dilate(hm, np.ones((3, 3), np.uint8))
        m = m * (1 - hm)
    # keep largest component (+ anything touching it after a small dilation)
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8))
    if n > 2:
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
        keep = (lab == k).astype(np.uint8)
        near = cv2.dilate(keep, np.ones((7, 7), np.uint8))
        for c in range(1, n):
            if c != k and (near[lab == c].any()) and st[c, cv2.CC_STAT_AREA] > 30:
                keep[lab == c] = 1
        m = keep.astype(np.float32)
    meta = json.load(open(f'{HD}/{i:04d}.json'))
    x0, y0 = meta['x0'], meta['y0']
    hr = cv2.imread(f'{HD}/{i:04d}.png', cv2.IMREAD_UNCHANGED)[..., ::-1].astype(np.float32) / 65535.0
    mcrop = m[y0:meta['y1'], x0:meta['x1']]
    f = a * K / 4.0                                   # hr -> sprite scale
    hr_s = cv2.resize(hr, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    # hr_s pixel v -> src x = x0 + (v+0.5)*sx/4 - 0.5 ; sprite p = K*(a*x + bx + 0.5) - 0.5
    sx = hr.shape[1] / hr_s.shape[1]; sy = hr.shape[0] / hr_s.shape[0]
    Ax = K * a * sx / 4.0; Ay = K * a * sy / 4.0
    Cx = K * (a * (x0 + sx / 8.0 - 0.5) + bx + 0.5) - 0.5
    Cy = K * (a * (y0 + sy / 8.0 - 0.5) + by + 0.5) - 0.5
    M = np.float32([[Ax, 0, Cx], [0, Ay, Cy]])
    spr = cv2.warpAffine(hr_s, M, (SW, SH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # alpha: resize binary mask to sprite scale (soft) then same placement
    ms = cv2.resize(mcrop, (hr_s.shape[1], hr_s.shape[0]), interpolation=cv2.INTER_LINEAR)
    ms = cv2.GaussianBlur(ms, (0, 0), 0.8)
    al = cv2.warpAffine(ms, M, (SW, SH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    spr = np.clip(spr, 0, 1).astype(np.float32)
    _bl = cv2.GaussianBlur(spr, (0, 0), 1.4)
    spr = np.clip(spr + 0.35 * (spr - _bl), 0, 1)
    # edge-aware refinement of the alpha with the SR image as guide
    al2 = guided(spr, al.astype(np.float32), 5, 2e-3)
    al2 = np.clip((al2 - 0.55) * 1.35 + 0.5, 0, 1)
    band = (al > 0.02) & (al < 0.98)
    band = cv2.dilate(band.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    alpha = np.where(band, al2, al).astype(np.float32)
    alpha = np.clip(alpha, 0, 1)
    fg = pymatting.estimate_foreground_ml(spr.astype(np.float64), alpha.astype(np.float64))
    fg = np.clip(fg, 0, 1).astype(np.float32)
    rgba = np.dstack([fg, alpha])
    cv2.imwrite(f'{SD}/{i:04d}.png', (rgba[..., [2, 1, 0, 3]] * 65535 + 0.5).astype(np.uint16))
    # low-res canonical version for optical flow
    lr = cv2.resize(rgba, (CW, CH), interpolation=cv2.INTER_AREA)
    np.save(f'{LD}/{i:04d}.npy', lr.astype(np.float16))
    print(i, round(time.time() - t0, 2), mcrop.shape, flush=True)
