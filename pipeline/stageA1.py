"""A1: super-resolve (x4) a generous crop around the product in each source frame."""
import sys, os, json, numpy as np, cv2, time, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtools
torch.set_num_threads(int(os.environ.get('NT', '1')))
net = vtools.load_sr('general', float(os.environ.get('DN', '0.25')))
os.makedirs('hr', exist_ok=True)
lo, hi = int(sys.argv[1]), int(sys.argv[2])
for i in range(lo, hi + 1):
    if os.path.exists(f'hr/{i:04d}.json'):
        continue
    while not os.path.exists(f'masks_fwd/{i + 1:04d}.png') and i < 394 and not os.path.exists('masks_done'):
        time.sleep(5)
    t0 = time.time()
    src = cv2.imread(f'full/{i:04d}.png')[..., ::-1].astype(np.float32) / 255
    m = (cv2.imread(f'masks_fwd/{i:04d}.png', 0) > 127).astype(np.uint8)
    ys, xs = np.nonzero(m)
    H, W = m.shape
    x0 = max(0, xs.min() - 24); x1 = min(W, xs.max() + 25)
    y0 = max(0, ys.min() - 24); y1 = min(H, ys.max() + 25)
    crop = np.ascontiguousarray(src[y0:y1, x0:x1])
    with torch.no_grad():
        hr = vtools.sr(net, crop)
    cv2.imwrite(f'hr/{i:04d}.png', (hr[..., ::-1] * 65535 + 0.5).astype(np.uint16))
    json.dump(dict(x0=int(x0), y0=int(y0), x1=int(x1), y1=int(y1)), open(f'hr/{i:04d}.json', 'w'))
    print(i, round(time.time() - t0, 2), crop.shape, flush=True)
