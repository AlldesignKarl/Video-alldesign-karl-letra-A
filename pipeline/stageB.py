"""Stage B: retimed product rotation (RIFE flow on LR canon frames, applied to HR sprites),
composited on the rendered set with depth-aware dolly-in, shadows, grade, grain and typography."""
import sys, os, json, math, numpy as np, cv2, torch, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch.nn.functional as F
import overlay
torch.set_num_threads(int(os.environ.get('NT', '4')))
cv2.setNumThreads(int(os.environ.get('NT', '4')))

FPS = 30
W, H = 1080, 1920
RS = 1.2                                   # render scale (bg is 1296x2304)
CW, CH, AX, AY = 420, 440, 210, 370
K = 2.05
SPR_ANCHOR = (K * (AX + 0.5) - 0.5, K * (AY + 0.5) - 0.5)
BASE0 = np.array([540.0, 1354.3])          # plinth-top centre at zoom 1 (final px)
PP = np.array([540.0, 960.0])              # principal point
Z_BASE = 1.14
DOLLY = 0.075                              # metres of push-in over the spot
DUR = 20.5
NFR = int(round(DUR * FPS))
ELL = dict(rx=360.4, ry_back=131.4, ry_front=160.3)

tm = json.load(open('timemap.json'))       # per output frame: float source index (1-based)
SCREEN_SCALE = float(json.load(open('xforms_meta.json'))['screen_scale'])

T = dict(title=(0.40, 3.05), craft=(3.35, 7.40), spray=5.0, excl=(7.75, 17.25), store1=10.55, store2=14.15,
         end=(17.65, 21.0), wait=18.45)
ELS = overlay.build_elements(T)


def srgb2lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def lin2srgb(x):
    x = np.clip(x, 0, None)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


# ------------------------------------------------------------------ background + depth
bg = cv2.imread('bg_full.png', cv2.IMREAD_UNCHANGED)[..., :3][..., ::-1].astype(np.float32) / 65535.0
bg_lin = srgb2lin(bg).astype(np.float32)
dep = np.load('bg_depth.npy').astype(np.float32)
dep = cv2.resize(dep, (bg.shape[1], bg.shape[0]), interpolation=cv2.INTER_LINEAR)
dep = cv2.GaussianBlur(dep, (0, 0), 2.0)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u - math.sin(2 * math.pi * u) / (2 * math.pi)


def dolly_at(t):
    return DOLLY * ease(t / DUR)


def warp_bg(delta):
    # output px p (final coords) -> source (zoom-1 final coords) q = PP + (p-PP)/s(z)
    def sz(z):
        return z / (z - delta)
    qx, qy = xx.copy(), yy.copy()
    for _ in range(3):
        z = cv2.remap(dep, (qx * RS + (RS - 1) / 2), (qy * RS + (RS - 1) / 2), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        s = sz(z)
        qx = (PP[0] + (xx - PP[0]) / s).astype(np.float32)
        qy = (PP[1] + (yy - PP[1]) / s).astype(np.float32)
    mx = ((qx + 0.5) * RS - 0.5).astype(np.float32)
    my = ((qy + 0.5) * RS - 0.5).astype(np.float32)
    return cv2.remap(bg_lin, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ sprites + RIFE
_spr_cache = {}


def load_sprite(i):
    if i not in _spr_cache:
        if len(_spr_cache) > 6:
            _spr_cache.pop(next(iter(_spr_cache)))
        s = cv2.imread(f'sprites/{i:04d}.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535.0
        s = s[..., [2, 1, 0, 3]]
        lr = np.load(f'lr/{i:04d}.npy').astype(np.float32)
        _spr_cache[i] = (s, lr)
    return _spr_cache[i]


_rife = None


def rife():
    global _rife
    if _rife is None:
        import vtools
        _rife = vtools.Rife()
    return _rife


def lr_for_flow(lr):
    a = lr[..., 3:4]
    return (lr[..., :3] * a + 0.5 * (1 - a)).astype(np.float32)


def sprite_at(sidx):
    nmax = len(os.listdir('sprites'))
    i = int(math.floor(sidx)); fr = sidx - i
    i = max(1, min(i, nmax))
    if fr < 0.02 or i >= nmax:
        return load_sprite(i)[0]
    if fr > 0.98:
        return load_sprite(i + 1)[0]
    s0, l0 = load_sprite(i); s1, l1 = load_sprite(i + 1)
    r = rife()
    a, b = lr_for_flow(l0), lr_for_flow(l1)
    h, w = a.shape[:2]
    pw, ph = math.ceil(w / 64) * 64, math.ceil(h / 64) * 64
    pad = (0, pw - w, 0, ph - h)
    A = F.pad(torch.from_numpy(a).permute(2, 0, 1)[None], pad)
    B = F.pad(torch.from_numpy(b).permute(2, 0, 1)[None], pad)
    div, grid = r._grid(ph, pw)
    ts = torch.full([1, 1, ph, pw], float(fr))
    with torch.no_grad():
        _, flow, mask = r.net(A, B, ts, div, grid, r.enc(A), r.enc(B))
    flow = flow[:, :, :h, :w]; mask = mask[:, :, :h, :w]
    SH, SW = s0.shape[:2]
    fl = F.interpolate(flow, size=(SH, SW), mode='bilinear', align_corners=False)
    fl = fl * torch.tensor([SW / w, SH / h, SW / w, SH / h]).view(1, 4, 1, 1)
    mk = F.interpolate(mask, size=(SH, SW), mode='bilinear', align_corners=False)
    gx = torch.linspace(-1, 1, SW).view(1, 1, 1, SW).expand(1, 1, SH, SW)
    gy = torch.linspace(-1, 1, SH).view(1, 1, SH, 1).expand(1, 1, SH, SW)
    g = torch.cat([gx, gy], 1)
    dv = torch.tensor([(SW - 1) / 2.0, (SH - 1) / 2.0]).view(1, 2, 1, 1)

    def wp(img, f):
        x = torch.from_numpy(img).permute(2, 0, 1)[None]
        # premultiply so colour and alpha warp consistently
        x = torch.cat([x[:, :3] * x[:, 3:4], x[:, 3:4]], 1)
        gg = (g + f / dv).permute(0, 2, 3, 1)
        return F.grid_sample(x, gg, mode='bicubic', padding_mode='border', align_corners=True)
    o = wp(s0, fl[:, :2]) * mk + wp(s1, fl[:, 2:4]) * (1 - mk)
    o = o[0].permute(1, 2, 0).numpy()
    al = np.clip(o[..., 3:4], 0, 1)
    rgb = np.where(al > 1e-4, o[..., :3] / np.maximum(al, 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 1), al]).astype(np.float32)


# ------------------------------------------------------------------ product look
def grade_product(spr):
    rgb, a = spr[..., :3], spr[..., 3]
    lin = srgb2lin(rgb)
    lin = lin * np.array([1.025, 1.0, 0.955], np.float32) * 0.88        # warm WB match to the set
    lum = (lin * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    lin = lum + (lin - lum) * 0.95
    h, w = a.shape
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    key = 1.06 - 0.12 * xs - 0.04 * ys                                  # soft window key from upper-left
    lin = lin * key
    # warm rim from the window side: left/top edges of the silhouette
    ab = cv2.GaussianBlur(a, (0, 0), 3.0)
    edge = np.clip(ab - np.roll(ab, 6, axis=1), 0, 1) + 0.5 * np.clip(ab - np.roll(ab, 6, axis=0), 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 2.0) * a
    lum = (lin * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    lin = lin + edge[..., None] * np.array([0.07, 0.06, 0.045], np.float32) * np.clip(1 - lum, 0, 1)
    # soft highlight shoulder so whites keep their texture
    kn = 0.72
    lin = np.where(lin > kn, kn + (1 - np.exp(-(lin - kn) / 0.3)) * 0.3, lin)
    return lin.astype(np.float32), a.astype(np.float32)


def shadow_mult(a_screen, base, scale):
    """multiplicative shadow layer (HxW) from the product alpha already placed in screen space."""
    sh = np.ones((H, W), np.float32)
    bx, by = float(base[0]), float(base[1])
    ys, xs = np.nonzero(a_screen > 0.5)
    if len(ys) == 0:
        return sh
    ytop = ys.min()
    hgt = by - ytop
    # 1) contact AO: bottom 10% of silhouette, squashed onto the plane
    band = a_screen.copy(); band[: int(by - 0.10 * hgt)] = 0
    M = np.float32([[1.03, 0, -0.03 * bx], [0, 0.45, 0.55 * by]])
    c1 = cv2.warpAffine(band, M, (W, H))
    c1 = cv2.GaussianBlur(c1, (0, 0), 5 * scale)
    c2 = cv2.GaussianBlur(cv2.warpAffine(band, np.float32([[1.15, 0, -0.15 * bx], [0, 0.6, 0.4 * by]]), (W, H)), (0, 0), 18 * scale)
    # 2) soft cast shadow falling back-right (key light front-left)
    M2 = np.float32([[1.0, -0.55, 0.55 * by], [0, 0.20, 0.80 * by]])
    c3 = cv2.warpAffine(a_screen, M2, (W, H))
    c3 = cv2.GaussianBlur(c3, (0, 0), 16 * scale)
    # clip to the plinth top ellipse (shadow can't hang in the air)
    e = ELL
    dx = (xx - bx) / (e['rx'] * scale)
    dy = (yy - by) / np.where(yy < by, e['ry_back'] * scale, e['ry_front'] * scale)
    inside = np.clip((1 - np.sqrt(dx * dx + dy * dy)) * 60, 0, 1)
    band0 = a_screen.copy(); band0[: int(by - 0.035 * hgt)] = 0
    c0 = cv2.warpAffine(band0, np.float32([[1.0, 0, 0], [0, 0.3, 0.7 * by]]), (W, H))
    c0 = cv2.GaussianBlur(c0, (0, 0), 2.2 * scale)
    # footprint ambient-occlusion ellipse
    bys, bxs = np.nonzero(band > 0.5)
    if len(bxs):
        fx0, fx1 = bxs.min(), bxs.max(); fw = fx1 - fx0
        ell = np.zeros((H, W), np.float32)
        cv2.ellipse(ell, (int((fx0 + fx1) / 2), int(by - 10 * scale)), (int(fw * 0.56), int(18 * scale + 0.10 * fw)), 0, 0, 360, 1.0, -1)
        ell = cv2.GaussianBlur(ell, (0, 0), 13 * scale)
        sh *= 1 - 0.36 * ell * inside
    sh *= 1 - 0.65 * np.clip(c0 * 1.5, 0, 1)
    sh *= 1 - 0.70 * np.clip(c1 * 1.3, 0, 1)
    sh *= 1 - 0.36 * np.clip(c2, 0, 1) * inside
    sh *= 1 - 0.32 * np.clip(c3, 0, 1) * inside
    return sh


def place(lin, a, base, scale):
    """resample product into screen space with its anchor at `base`."""
    M = np.float32([[scale, 0, base[0] - SPR_ANCHOR[0] * scale], [0, scale, base[1] - SPR_ANCHOR[1] * scale]])
    pm = cv2.warpAffine(np.dstack([lin * a[..., None], a]), M, (W, H), flags=cv2.INTER_CUBIC)
    return np.clip(pm[..., :3], 0, None), np.clip(pm[..., 3], 0, 1)


# ------------------------------------------------------------------ finishing
vig = None


def finish(rgb_lin, t, k):
    global vig
    if vig is None:
        r = np.sqrt(((xx - 540) / 540) ** 2 + ((yy - 1000) / 1050) ** 2)
        vig = (1 - 0.16 * np.clip(r - 0.35, 0, None) ** 1.6).astype(np.float32)
    x = rgb_lin * vig[..., None]
    s = lin2srgb(x)
    # gentle film curve + warm split tone
    s = s + 0.035 * np.sin(np.pi * s) * (s - 0.5) * -1.0
    s = s * np.array([1.0, 0.99, 0.965], np.float32) + np.array([0.012, 0.008, 0.0], np.float32)
    s = np.clip(s, 0, 1)
    # typography
    L = overlay.render(ELS, t)
    s = L[..., :3] + s * (1 - L[..., 3:4])
    # fine grain (temporal)
    rng = np.random.default_rng(1000 + k)
    gr = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    gr = cv2.resize(gr, (W, H), interpolation=cv2.INTER_LINEAR)
    lum = s.mean(-1, keepdims=True)
    s = s + gr[..., None] * (0.010 * (1 - np.abs(lum - 0.5) * 1.2))
    # fades from / to black
    f = min(1.0, t / 0.55) * min(1.0, max(0.0, (DUR - t) / 0.85))
    f = f * f * (3 - 2 * f)
    s = s * f
    return np.clip(s, 0, 1)


def main(lo, hi):
    os.makedirs('out', exist_ok=True)
    for k in range(lo, hi):
        fn = f'out/{k:04d}.png'
        if os.path.exists(fn):
            continue
        t0 = time.time()
        t = k / FPS
        delta = dolly_at(t)
        frame = warp_bg(delta)
        s_near = Z_BASE / (Z_BASE - delta)
        base = PP + (BASE0 - PP) * s_near
        spr = sprite_at(tm[k])
        lin, a = grade_product(spr)
        scale = SCREEN_SCALE * s_near
        pl, pa = place(lin, a, base, scale)
        frame = frame * shadow_mult(pa, base, s_near)[..., None]
        frame = pl + frame * (1 - pa[..., None])
        out = finish(frame, t, k)
        cv2.imwrite(fn, (out[..., ::-1] * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])
        print(k, round(time.time() - t0, 2), flush=True)


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
