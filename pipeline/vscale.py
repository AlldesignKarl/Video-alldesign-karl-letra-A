import cv2, numpy as np, glob
files = sorted(glob.glob('masks_fwd/*.png')); N = len(files)
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
prev = cv2.cvtColor(cv2.imread('full/0001.png'), cv2.COLOR_BGR2GRAY)
logS = [0.0]; ty = [0.0]; coefs = []
for i in range(1, N):
    cur = cv2.cvtColor(cv2.imread(f'full/{i + 1:04d}.png'), cv2.COLOR_BGR2GRAY)
    m = cv2.imread(f'masks_fwd/{i:04d}.png', 0) > 127
    m = cv2.erode(m.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    fl = dis.calc(prev, cur, None)
    ys, xs = np.nonzero(m)
    vy = fl[ys, xs, 1]
    y = ys.astype(float); ym = y.mean()
    A = np.stack([y - ym, np.ones_like(y)], 1)
    keep = np.ones(len(y), bool)
    for _ in range(3):
        coef, *_ = np.linalg.lstsq(A[keep], vy[keep], rcond=None)
        res = np.abs(A @ coef - vy)
        keep = res < max(0.5, np.percentile(res, 80))
    coefs.append((coef[0], coef[1], ym))
    logS.append(logS[-1] + np.log1p(coef[0]))
    ty.append(coef[1])
    prev = cur
S = np.exp(np.array(logS))
np.save('vscale.npy', S); np.save('vcoefs.npy', np.array(coefs))
rows = np.load('rot_rows.npy')
for i in range(0, min(N, len(rows)), 15):
    print(i + 1, round(S[i], 4), 'h', int(rows[i, 1] - rows[i, 0]), 'h/S', round((rows[i, 1] - rows[i, 0]) / S[i], 1))
