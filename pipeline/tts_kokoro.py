import soundfile as sf, numpy as np, sys
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
lines = ["Estos son los Ambientadores del Cachirulo.",
 "Elaborados de forma artesanal, con pulverizador de diez mililitros.",
 "En exclusiva, en nuestras tiendas colaboradoras:",
 "Mercería El Siglo, en Cortes de Aragón, cuarenta y seis.",
 "Y Papelería Casablanca, en calle La Vía, dieciséis.",
 "Descúbrelos. Te esperamos."]
sp=float(sys.argv[1]); v=sys.argv[2]
tot=0
for i,l in enumerate(lines):
    a, sr = k.create(l, voice=v, speed=sp, lang="es")
    e=np.where(np.abs(a)>0.008)[0]; a=a[max(0,e[0]-240):e[-1]+1200]
    sf.write(f'v_{v}_{i}.wav', a, sr); tot+=len(a)/sr
    print(i, round(len(a)/sr,2), k.tokenizer.phonemize(l, 'es') if hasattr(k,'tokenizer') else '')
print('total speech', round(tot,2))
