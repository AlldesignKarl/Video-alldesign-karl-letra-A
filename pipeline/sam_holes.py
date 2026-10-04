import numpy as np, cv2, json, os, time
from ultralytics.models.sam import SAM2VideoPredictor
p = json.load(open('hole_prompt.json'))
os.makedirs('holes', exist_ok=True)
ov = dict(conf=0.25, task="segment", mode="predict", imgsz=1024, model="models/sam2.1_l.pt", verbose=False, save=False)
pred = SAM2VideoPredictor(overrides=ov)
t = time.time(); n = 0
for r in pred(source='rev_clip.mp4', points=p['pts'], labels=p['lab'], stream=True):
    idx = 259 - n
    if r.masks is None:
        m = np.zeros((850, 478), np.uint8)
    else:
        m = (r.masks.data.cpu().numpy().max(0) > 0).astype(np.uint8)
    cv2.imwrite(f'holes/{idx:04d}.png', m * 255)
    n += 1
    if n % 10 == 0: print(n, idx, round(time.time() - t, 1), int(m.sum()), flush=True)
print('done', n, flush=True)
