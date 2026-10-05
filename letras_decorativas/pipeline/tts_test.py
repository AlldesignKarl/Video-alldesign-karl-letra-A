import numpy as np, soundfile as sf, sys, json
from kokoro_onnx import Kokoro
k=Kokoro('kokoro.onnx','voices.npz')
lines=json.load(open(sys.argv[1])); voice=sys.argv[2]; sp=float(sys.argv[3]); tag=sys.argv[4]
tot=0
for i,l in enumerate(lines):
    a,sr=k.create(l,voice=voice,speed=sp,lang='es')
    e=np.where(np.abs(a)>0.008)[0]; a=a[max(0,e[0]-240):e[-1]+1200]
    sf.write(f'{tag}_{i}.wav',a,sr); tot+=len(a)/sr
    print(i,round(len(a)/sr,2),l)
print('total',round(tot,2))
