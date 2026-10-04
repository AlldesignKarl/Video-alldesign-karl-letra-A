import numpy as np, cv2, glob, json
files = sorted(glob.glob('masks_fwd/*.png'))
rows = []
for f in files:
    m = (cv2.imread(f, 0) > 127).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); mm = lab == k
    ys, xs = np.nonzero(mm); y1 = ys.max(); y0 = ys.min()
    low = mm[int(y1 - 0.40 * 290):y1 + 1]
    c = np.nonzero(low.any(0))[0]
    xl, xr = c.min(), c.max()
    rows.append([int(y0), int(y1), int(xl), int(xr), float((xl + xr) / 2), int(xr - xl + 1)])
rows = np.array(rows, float)
np.save('rot_rows.npy', rows)
for i in range(0, len(rows), 8):
    r = rows[i]; print(i + 1, 'y0', int(r[0]), 'y1', int(r[1]), 'axis', round(r[4], 1), 'fw', int(r[5]))
