"""A1 (v2): multi-frame fusion (±3 frames, flow-aligned) then Real-ESRGAN x4 of the product crop."""
import sys, os, json, numpy as np, cv2, time, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtools, fuse
torch.set_num_threads(int(os.environ.get('NT', '2')))
net = vtools.load_sr('general', float(os.environ.get('DN', '0.25')))
os.makedirs('hr2', exist_ok=True)
lo, hi = int(sys.argv[1]), int(sys.argv[2])
for i in range(lo, hi + 1):
    if os.path.exists(f'hr2/{i:04d}.json'):
        continue
    t0 = time.time()
    meta = json.load(open(f'hr/{i:04d}.json'))
    x0, y0, x1, y1 = meta['x0'], meta['y0'], meta['x1'], meta['y1']
    F = fuse.fuse(i, x0, y0, x1, y1)
    crop = np.ascontiguousarray(F[y0:y1, x0:x1, ::-1])
    with torch.no_grad():
        hr = vtools.sr(net, crop)
    cv2.imwrite(f'hr2/{i:04d}.png', (hr[..., ::-1] * 65535 + 0.5).astype(np.uint16))
    json.dump(meta, open(f'hr2/{i:04d}.json', 'w'))
    print(i, round(time.time() - t0, 2), flush=True)
