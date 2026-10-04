import numpy as np, cv2, time, sys, os
from ultralytics.models.sam import SAM2VideoPredictor
src, init_mask, outdir, reverse = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]=='1'
os.makedirs(outdir, exist_ok=True)
mk=np.zeros((850,478),np.uint8)
ov = dict(conf=0.25, task="segment", mode="predict", imgsz=1024, model="models/sam2.1_l.pt", verbose=False, save=False)
p = SAM2VideoPredictor(overrides=ov)
t=time.time(); n=0
N=394
import json
pr=json.load(open(init_mask))
for r in p(source=src, bboxes=pr['box'], points=pr['pts'], labels=pr['lab'], stream=True):
    if r.masks is None:
        m = np.zeros(mk.shape, np.uint8)
    else:
        m = (r.masks.data.cpu().numpy().max(0)>0).astype(np.uint8)
    idx = (N-1-n) if reverse else n
    cv2.imwrite(f'{outdir}/{idx+1:04d}.png', m*255)
    n+=1
    if n%20==0: print(n, time.time()-t, flush=True)
print('done', n, time.time()-t)
