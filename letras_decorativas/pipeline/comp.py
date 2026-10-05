"""Spot compositor: the three real photographs of the letter (cut out), placed on the rendered set,
filmed by a continuous virtual camera (dolly + orbit drift with depth parallax), joined with soft
dissolves during the close-ups. Product 2.5D turn = perspective homography of a few degrees."""
import os, sys, json, math, time
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overlay2 as overlay
cv2.setNumThreads(int(os.environ.get('NT', '2')))

W, H, FPS, DUR = 1080, 1920, 30, 20.0
NFR = int(round(DUR * FPS))
CEN = np.array([540.0, 960.0])
BGD = os.environ.get('BG_DIR', '../bg')
CUT = os.environ.get('CUT_DIR', '../cut')
OD = os.environ.get('OUT_DIR', 'frames')
BG_SUFFIX = os.environ.get('BG_SUFFIX', '')          # '' final renders, 'prev' quick previews

# ------------------------------------------------------------------ timeline
# segments: view, bg elevation, sprite base anchor (source px), scale (screen px per source px),
# time window [t0, t1] (cross-dissolves where windows overlap), turn angle (rad) at t0 / t1
SEG = [
    dict(v='v1', el=14, anchor=(722, 1130), k=0.94, t=(0.0, 5.05), th=(-0.055, 0.050)),
    dict(v='v2', el=30, anchor=(560, 1065), k=0.82, t=(3.95, 10.05), th=(-0.040, 0.045)),
    dict(v='v3', el=14, anchor=(700, 1348), k=0.684, t=(8.95, 20.0), th=(-0.060, 0.055)),
]
XF = [(3.95, 5.05), (8.95, 10.05)]                       # dissolve windows
BASE = {14: np.array([540.0, 1559.6]), 30: np.array([540.0, 1491.3])}   # world origin on screen (zoom 1)

# camera keys: t, zoom, centre (zoom-1 screen coords)
CAM = [
    (0.0, 1.08, 540, 1010), (2.3, 1.15, 548, 1040), (4.5, 1.55, 560, 1290),
    (5.3, 1.58, 425, 1135), (6.8, 1.50, 445, 1115), (9.0, 1.12, 540, 1030),
    (10.0, 1.62, 470, 1095), (11.9, 1.52, 650, 1180), (14.0, 1.04, 585, 968),
    (20.0, 1.08, 585, 975),
]
PAN = [(0.0, 120.0), (20.0, -125.0)]                 # lateral orbit drift of the far wall (px, zoom 1)
Z_AXIS = 1.25                                        # camera-to-product distance in the set (m)

TXT = dict(title=(0.45, 2.55), artesanales=(4.55, 6.85), detalle=(7.15, 9.35),
           stores=(12.35, 21.0), store1=12.7, store2=16.2)
ELS = overlay.build_elements(TXT)


def srgb2lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def lin2srgb(x):
    x = np.clip(x, 0, None)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def smooth_keys(keys, t):
    """C1-continuous interpolation through keys (cubic Hermite, Catmull-Rom tangents, zero at ends)."""
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return np.array(keys[0][1:], np.float64)
    if t >= ts[-1]:
        return np.array(keys[-1][1:], np.float64)
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    P = [np.array(k[1:], np.float64) for k in keys]
    t0, t1 = ts[i], ts[i + 1]; h = t1 - t0; u = (t - t0) / h

    def tan(j):
        if j == 0 or j == len(ts) - 1:
            return np.zeros_like(P[j])
        return (P[j + 1] - P[j - 1]) / (ts[j + 1] - ts[j - 1]) * 0.85
    m0, m1 = tan(i) * h, tan(i + 1) * h
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return h00 * P[i] + h10 * m0 + h01 * P[i + 1] + h11 * m1


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ background
_bg = {}


def load_bg(el):
    if el not in _bg:
        name = f'{BGD}/bg{el}{BG_SUFFIX}.png' if not BG_SUFFIX else f'{BGD}/prev{el}.png'
        im = cv2.imread(name, cv2.IMREAD_UNCHANGED)[..., :3][..., ::-1]
        im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
        dp = f'{BGD}/dep{el}.exr'
        if os.path.exists(dp) and not BG_SUFFIX:
            import OpenEXR
            d = OpenEXR.File(dp).channels()['RGBA'].pixels[..., 0].astype(np.float32) * 10.0
            d[d < 0.05] = 6.0                                # rays that hit nothing: far
            d = cv2.resize(d, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_LINEAR)
        else:  # rough stand-in: table rows get nearer towards the bottom, wall is far
            hh = im.shape[0]
            d = np.tile(np.linspace(3.2, 0.9, hh, dtype=np.float32)[:, None], (1, im.shape[1]))
        d = cv2.GaussianBlur(np.clip(d, 0.3, 6.0), (0, 0), 3.0)
        _bg[el] = (srgb2lin(im), d, im.shape[0] / H)
    return _bg[el]


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def warp_bg(el, Z, C, pan):
    """camera dolly towards the product (depth-correct magnification) + lateral orbit parallax."""
    img, dep, RS = load_bg(el)
    BH, BW = img.shape[:2]
    delta = Z_AXIS * (1 - 1 / Z)                          # how far the camera has moved in (m)
    qx = (C[0] + (xx - CEN[0]) / Z).astype(np.float32)
    qy = (C[1] + (yy - CEN[1]) / Z).astype(np.float32)
    for _ in range(3):
        bx = ((qx - CEN[0]) * RS + BW / 2).astype(np.float32); by = ((qy - CEN[1]) * RS + BH / 2).astype(np.float32)
        z = cv2.remap(dep, bx, by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        s = np.clip(z / np.maximum(z - delta, 0.05), 0.5, 4.0)
        par = (1 - Z_AXIS / z)                                             # 0 at the product, ->1 far away
        qx = (C[0] + (xx - CEN[0]) / s - pan * par).astype(np.float32)
        qy = (C[1] + (yy - CEN[1]) / s).astype(np.float32)
    bx = ((qx - CEN[0]) * RS + BW / 2).astype(np.float32); by = ((qy - CEN[1]) * RS + BH / 2).astype(np.float32)
    return cv2.remap(img, bx, by, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ product sprites
_spr = {}
META = json.load(open(f'{CUT}/spr_meta.json'))


def load_spr(v):
    if v not in _spr:
        s = cv2.imread(f'{CUT}/spr_{v}.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535.0
        rgb = s[..., :3][..., ::-1]; a = s[..., 3:4]
        lin = grade_product(srgb2lin(rgb), a[..., 0])
        _spr[v] = np.dstack([lin * a, a]).astype(np.float32)          # premultiplied, linear
    return _spr[v]


def grade_product(lin, a):
    lin = lin * np.array([1.02, 1.0, 0.97], np.float32)                 # match the warm set
    lum = (lin * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    lin = lum + (lin - lum) * 0.97
    h, w = a.shape
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]; ys = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    lin = lin * (1.04 - 0.08 * xs - 0.03 * ys)                         # soft key from upper-left, like the set
    # fine detail pass inside the silhouette only (no halos)
    inner = cv2.erode((a > 0.95).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
    inner = cv2.GaussianBlur(inner, (0, 0), 2.0)[..., None]
    lin = lin + 0.35 * inner * (lin - cv2.GaussianBlur(lin, (0, 0), 1.2))
    lin = lin + 0.12 * inner * (lin - cv2.GaussianBlur(lin, (0, 0), 7.0))
    lin = np.clip(lin, 0, None)
    kn = 0.75
    return np.where(lin > kn, kn + (1 - np.exp(-(lin - kn) / 0.28)) * 0.28, lin).astype(np.float32)


def product_matrix(seg, th, Z, C):
    m = META[seg['v']]
    ax, ay = seg['anchor'][0] - m['x0'], seg['anchor'][1] - m['y0']   # anchor in sprite px
    f = 2600.0
    # rotation about the vertical axis through the anchor (perspective of a turn by th)
    T0 = np.array([[1, 0, -ax], [0, 1, -ay], [0, 0, 1]], np.float64)
    c, s = math.cos(th), math.sin(th)
    R = np.array([[c, 0, 0], [0, 1, 0], [-s / f, 0, 1]], np.float64)
    k = seg['k']
    B = BASE[seg['el']]
    S = np.array([[k * Z, 0, (B[0] - C[0]) * Z + CEN[0]], [0, k * Z, (B[1] - C[1]) * Z + CEN[1]], [0, 0, 1]], np.float64)
    return S @ R @ T0


def shadow_mult(a, base, Z, k):
    """contact occlusion + soft cast shadow (key light front-left -> shadow falls back-right)."""
    sh = np.ones((H, W), np.float32)
    ys, xs = np.nonzero(a > 0.5)
    if len(ys) == 0:
        return sh
    bx, by = float(base[0]), float(base[1])
    hgt = max(by - ys.min(), 50)
    sc = Z * k / 0.9
    band = a.copy(); band[: int(max(0, by - 0.09 * hgt))] = 0
    c0 = cv2.GaussianBlur(cv2.warpAffine(band, np.float32([[1.0, 0, 0], [0, 0.32, 0.68 * by]]), (W, H)), (0, 0), 2.5 * sc)
    c1 = cv2.GaussianBlur(cv2.warpAffine(band, np.float32([[1.04, 0, -0.04 * bx], [0, 0.45, 0.55 * by]]), (W, H)), (0, 0), 7 * sc)
    c2 = cv2.GaussianBlur(cv2.warpAffine(band, np.float32([[1.18, 0, -0.18 * bx], [0, 0.65, 0.35 * by]]), (W, H)), (0, 0), 22 * sc)
    c3 = cv2.GaussianBlur(cv2.warpAffine(a, np.float32([[1.0, -0.50, 0.50 * by], [0, 0.17, 0.83 * by]]), (W, H)), (0, 0), 20 * sc)
    sh *= 1 - 0.55 * np.clip(c0 * 1.5, 0, 1)
    sh *= 1 - 0.45 * np.clip(c1 * 1.3, 0, 1)
    sh *= 1 - 0.30 * np.clip(c2, 0, 1)
    sh *= 1 - 0.26 * np.clip(c3, 0, 1)
    return sh


def render_seg(seg, t, Z, C, pan):
    th = seg['th'][0] + (seg['th'][1] - seg['th'][0]) * ease((t - seg['t'][0]) / (seg['t'][1] - seg['t'][0]))
    bg = warp_bg(seg['el'], Z, C, pan)
    spr = load_spr(seg['v'])
    M = product_matrix(seg, th, Z, C)
    pm = cv2.warpPerspective(spr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    rgb = np.clip(pm[..., :3], 0, None); a = np.clip(pm[..., 3], 0, 1)
    base = (BASE[seg['el']] - C) * Z + CEN
    bg = bg * shadow_mult(a, base, Z, seg['k'])[..., None]
    # light wrap: a little of the blurred set light spills over the silhouette edge
    wrap = cv2.GaussianBlur(bg, (0, 0), 6) * (cv2.GaussianBlur(1 - a, (0, 0), 3) * a)[..., None] * 0.18
    return rgb + wrap + bg * (1 - a[..., None])


vig = None


def finish(lin, t, k):
    global vig
    if vig is None:
        r = np.sqrt(((xx - 540) / 540) ** 2 + ((yy - 1050) / 1100) ** 2)
        vig = (1 - 0.14 * np.clip(r - 0.4, 0, None) ** 1.6).astype(np.float32)
    s = lin2srgb(lin * vig[..., None])
    s = s + 0.03 * np.sin(np.pi * s) * (0.5 - s)                           # gentle film curve
    s = s * np.array([1.0, 0.985, 0.975], np.float32) + np.array([0.010, 0.004, 0.002], np.float32)
    s = np.clip(s, 0, 1)
    L = overlay.render(ELS, t)
    s = L[..., :3] + s * (1 - L[..., 3:4])
    rng = np.random.default_rng(500 + k)
    gr = cv2.resize(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    s = s + gr[..., None] * (0.0040 * (1 - np.abs(s.mean(-1, keepdims=True) - 0.5) * 1.2))
    f = min(1.0, t / 0.35) * min(1.0, max(0.0, (DUR - t) / 0.35))
    s = s * (f * f * (3 - 2 * f))
    return np.clip(s, 0, 1)


def frame(k):
    t = k / FPS
    Z, Cx, Cy = smooth_keys(CAM, t)
    pan = smooth_keys(PAN, t)[0]
    C = np.array([Cx, Cy])
    acc = None; wsum = 0.0
    for i, seg in enumerate(SEG):
        if not (seg['t'][0] <= t <= seg['t'][1]):
            continue
        w, blur = 1.0, 0.0
        if i > 0 and t < XF[i - 1][1]:            # incoming: comes back into focus
            u = (t - XF[i - 1][0]) / (XF[i - 1][1] - XF[i - 1][0])
            w = ease(u); blur = max(blur, ease(min(1.0, 2 * (1 - u))))
        if i < len(XF) and t > XF[i][0]:          # outgoing: drifts out of focus
            u = (t - XF[i][0]) / (XF[i][1] - XF[i][0])
            w = min(w, 1 - ease(u)); blur = max(blur, ease(min(1.0, 2 * u)))
        if w <= 0:
            continue
        img = render_seg(seg, t, Z, C, pan)
        if blur > 0.01:                           # rack-focus transition with a soft bloom
            sg = 16.0 * blur
            img = cv2.GaussianBlur(img, (0, 0), sg) * (1 + 0.05 * blur)
        acc = img * w if acc is None else acc + img * w
        wsum += w
    return finish(acc / wsum, t, k)


def main(lo, hi):
    os.makedirs(OD, exist_ok=True)
    for k in range(lo, hi):
        fn = f'{OD}/{k:04d}.png'
        if os.path.exists(fn):
            continue
        t0 = time.time()
        out = frame(k)
        cv2.imwrite(fn, (out[..., ::-1] * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])
        print(k, round(time.time() - t0, 2), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        for k in map(int, sys.argv[2:]):
            out = frame(k)
            cv2.imwrite(f'test_{k:04d}.jpg', (out[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        main(int(sys.argv[1]), int(sys.argv[2]))
