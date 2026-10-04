import math, torch, torch.nn as nn, torch.nn.functional as F, numpy as np, os
D = os.path.dirname(os.path.abspath(__file__))
torch.set_grad_enabled(False)

# ------------------------------------------------------------------ RIFE 4.25
from rifepkg.IFNet_HDv3_v4_25 import IFNet, Head
from rifepkg.warplayer import warp

class Rife:
    def __init__(self, path=f'{D}/rife/flownet_v4.25.pkl'):
        sd = torch.load(path, map_location='cpu')
        sd = {k.replace('module.', ''): v for k, v in sd.items() if 'module.' in k}
        self.net = IFNet(1, False); self.net.load_state_dict(sd, strict=False); self.net.eval()
        self.enc = Head(); self.enc.load_state_dict({k.replace('encode.', ''): v for k, v in sd.items() if 'encode.' in k}); self.enc.eval()
        self.cache = {}

    def _grid(self, ph, pw):
        key = (ph, pw)
        if key not in self.cache:
            div = torch.tensor([(pw - 1.0) / 2.0, (ph - 1.0) / 2.0])
            th = torch.linspace(-1, 1, pw).view(1, 1, 1, pw).expand(-1, -1, ph, -1)
            tv = torch.linspace(-1, 1, ph).view(1, 1, ph, 1).expand(-1, -1, -1, pw)
            self.cache[key] = (div, torch.cat([th, tv], 1))
        return self.cache[key]

    def interp(self, a, b, t, extra_a=None, extra_b=None):
        """a,b: float32 HxWx3 in [0,1]; extras: HxWxC arrays warped with same flow/mask."""
        h, w = a.shape[:2]
        pw, ph = math.ceil(w / 64) * 64, math.ceil(h / 64) * 64
        pad = (0, pw - w, 0, ph - h)
        A = F.pad(torch.from_numpy(a).permute(2, 0, 1)[None].float(), pad)
        B = F.pad(torch.from_numpy(b).permute(2, 0, 1)[None].float(), pad)
        div, grid = self._grid(ph, pw)
        ts = torch.full([1, 1, ph, pw], float(t))
        out, flow, mask = self.net(A, B, ts, div, grid, self.enc(A), self.enc(B))
        res = out[0, :, :h, :w].permute(1, 2, 0).clamp(0, 1).numpy()
        ex = None
        if extra_a is not None:
            EA = F.pad(torch.from_numpy(extra_a).permute(2, 0, 1)[None].float(), pad)
            EB = F.pad(torch.from_numpy(extra_b).permute(2, 0, 1)[None].float(), pad)
            m = torch.sigmoid(mask) if mask.min() < 0 or mask.max() > 1 else mask
            wa = warp(EA, flow[:, :2], div, grid); wb = warp(EB, flow[:, 2:4], div, grid)
            ex = (wa * m + wb * (1 - m))[0, :, :h, :w].permute(1, 2, 0).numpy()
        return res, ex

# ------------------------------------------------------------------ Real-ESRGAN
class SRVGGNetCompact(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList()
        self.body.append(nn.Conv2d(num_in_ch, num_feat, 3, 1, 1))
        self.body.append(nn.PReLU(num_parameters=num_feat))
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for l in self.body: out = l(out)
        return self.upsampler(out) + F.interpolate(x, scale_factor=self.upscale, mode='nearest')

class RDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1); self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1); self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1); self.lrelu = nn.LeakyReLU(0.2, True)
    def forward(self, x):
        x1 = self.lrelu(self.conv1(x)); x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1))); x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        return self.conv5(torch.cat((x, x1, x2, x3, x4), 1)) * 0.2 + x

class RRDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__(); self.rdb1 = RDB(nf, gc); self.rdb2 = RDB(nf, gc); self.rdb3 = RDB(nf, gc)
    def forward(self, x): return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x

class RRDBNet(nn.Module):
    def __init__(self, nf=64, nb=23, gc=32):
        super().__init__()
        self.conv_first = nn.Conv2d(3, nf, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1); self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1); self.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, True)
    def forward(self, x):
        feat = self.conv_first(x); feat = feat + self.conv_body(self.body(feat))
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode='nearest')))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode='nearest')))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))

def load_sr(kind='general', denoise=0.5):
    if kind == 'general':
        net = SRVGGNetCompact()
        a = torch.load(f'{D}/models/realesr-general-x4v3.pth', map_location='cpu')['params']
        b = torch.load(f'{D}/models/realesr-general-wdn-x4v3.pth', map_location='cpu')['params']
        # DNI: denoise strength s -> s*general + (1-s)*wdn  (as in Real-ESRGAN inference script)
        sd = {k: denoise * a[k] + (1 - denoise) * b[k] for k in a}
        net.load_state_dict(sd)
    else:
        net = RRDBNet()
        net.load_state_dict(torch.load(f'{D}/models/RealESRGAN_x4plus.pth', map_location='cpu')['params_ema'])
    return net.eval()

def sr(net, img, tile=0):
    """img float32 HxWx3 [0,1] RGB -> 4x"""
    x = torch.from_numpy(img).permute(2, 0, 1)[None].float()
    y = net(x)
    return y[0].permute(1, 2, 0).clamp(0, 1).numpy()
