import cv2, numpy as np, json, sys, time
from pymatting import estimate_alpha_cf, estimate_foreground_ml
cfg = json.load(open('holes.json'))
def run(n):
    im = cv2.imread(n + '.jpg'); h, w = im.shape[:2]
    U = np.load(n + '_mt.npy').max(0)
    m = (U > 0.5).astype(np.uint8)
    # keep the largest components (product), drop specks
    k, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for i in range(1, k):
        if st[i, 4] > 3000: keep[lab == i] = 1
    m = keep
    c = cfg[n]
    for poly in c.get('add', []):  # force-include regions (unknown -> let matting decide)
        cv2.fillPoly(m, [np.array(poly, np.int32)], 1)
    fg = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * c['er'] + 1,) * 2))
    bgz = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * c['di'] + 1,) * 2))
    tri = np.full((h, w), 0.5, np.float64)
    tri[fg > 0] = 1.0; tri[bgz == 0] = 0.0
    for poly in c.get('bg', []):   # holes: sure background core, with unknown border around
        pm = np.zeros((h, w), np.uint8); cv2.fillPoly(pm, [np.array(poly, np.int32)], 1)
        tri[cv2.dilate(pm, np.ones((2 * c['hb'] + 1,) * 2, np.uint8)) > 0] = 0.5
        tri[pm > 0] = 0.0
    for poly in c.get('cutbelow', []):  # everything under the base line is plate/reflection
        pm = np.zeros((h, w), np.uint8); cv2.fillPoly(pm, [np.array(poly, np.int32)], 1)
        tri[pm > 0] = 0.0
    ys, xs = np.nonzero(tri > 0)
    y0, y1, x0, x1 = max(0, ys.min() - 20), min(h, ys.max() + 20), max(0, xs.min() - 20), min(w, xs.max() + 20)
    I = im[y0:y1, x0:x1, ::-1].astype(np.float64) / 255
    T = tri[y0:y1, x0:x1]
    t = time.time()
    a = estimate_alpha_cf(I, T)
    F = estimate_foreground_ml(I, a)
    print(n, 'matte', round(time.time() - t, 1), 's', (x0, y0, x1, y1))
    A = np.zeros((h, w)); A[y0:y1, x0:x1] = a
    Fu = np.zeros((h, w, 3)); Fu[y0:y1, x0:x1] = F
    np.save(n + '_alpha.npy', A.astype(np.float32)); np.save(n + '_fg.npy', Fu.astype(np.float32))
    cv2.imwrite(n + '_tri.png', (tri * 255).astype(np.uint8))
    # check composite on a contrasting colour
    bgc = np.array([0.15, 0.35, 0.30])
    comp = Fu * A[..., None] + bgc * (1 - A[..., None])
    cv2.imwrite(n + '_check.jpg', (comp[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
for n in sys.argv[1:]: run(n)
