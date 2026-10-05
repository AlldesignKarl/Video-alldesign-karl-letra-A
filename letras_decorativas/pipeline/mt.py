import mediapipe as mp, numpy as np, cv2, sys, json
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.components import containers
opts=vision.InteractiveSegmenterOptions(base_options=mpp.BaseOptions(model_asset_path='magic_touch.tflite'),output_confidence_masks=True,output_category_mask=False)
seg=vision.InteractiveSegmenter.create_from_options(opts)
def run(name, pts):
    im=cv2.imread(name+'.jpg'); h,w=im.shape[:2]
    mpi=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(im,cv2.COLOR_BGR2RGB))
    outs=[]
    for (x,y) in pts:
        roi=vision.InteractiveSegmenterRegionOfInterest(format=vision.InteractiveSegmenterRegionOfInterest.Format.KEYPOINT,keypoint=containers.keypoint.NormalizedKeypoint(x/w,y/h))
        r=seg.segment(mpi,roi); m=r.confidence_masks[0].numpy_view().copy()
        outs.append(m)
    return np.stack(outs)
if __name__=='__main__':
    cfg=json.load(open('pts.json'))
    for n,pts in cfg.items():
        M=run(n,pts); np.save(n+'_mt.npy',M)
        im=cv2.imread(n+'.jpg')
        u=M.max(0)
        vis=(im*0.35+im*0.65*u[...,None]).astype(np.uint8)
        for (x,y) in pts: cv2.circle(vis,(x,y),8,(0,255,0),-1)
        cv2.imwrite(n+'_mt.jpg',vis)
        print(n, M.shape, [round(float((m>0.5).mean()),3) for m in M])
