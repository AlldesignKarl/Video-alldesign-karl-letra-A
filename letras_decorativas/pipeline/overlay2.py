"""On-screen typography for the decorative-letter spot (1080x1920)."""
from PIL import Image, ImageDraw, ImageFont
import numpy as np, os
FD = os.environ.get('FONT_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'))
F_SERIF = f'{FD}/CormorantGaramond%5Bwght%5D.ttf'
F_SERIF_I = f'{FD}/CormorantGaramond-Italic%5Bwght%5D.ttf'
F_SANS = f'{FD}/Montserrat%5Bwght%5D.ttf'
W, H = 1080, 1920
SS = 2
INK = (82, 42, 48)        # deep rose-brown
INK2 = (128, 82, 84)
RULE = (178, 126, 118)


def font(path, size, wght):
    f = ImageFont.truetype(path, size * SS)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def text_img(txt, fnt, color, tracking=0.0):
    size = fnt.size
    asc, desc = fnt.getmetrics()
    widths = [fnt.getlength(c) for c in txt]
    total = sum(widths) + tracking * size * (len(txt) - 1)
    pad = 10 * SS
    im = Image.new('RGBA', (int(total) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad
        for c, w in zip(txt, widths):
            d.text((x, pad), c, font=fnt, fill=color + (255,)); x += w + tracking * size
    else:
        d.text((pad, pad), txt, font=fnt, fill=color + (255,))
    im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    return im, (asc + pad) / SS


def rule_img(width, color=RULE, thick=1.6):
    im = Image.new('RGBA', (int(width * SS), int(8 * SS)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); y = 4 * SS
    gap = 9 * SS; cx = width * SS / 2; r = 3.4 * SS
    d.rectangle([0, y - thick * SS / 2, cx - gap, y + thick * SS / 2], fill=color + (255,))
    d.rectangle([cx + gap, y - thick * SS / 2, width * SS, y + thick * SS / 2], fill=color + (255,))
    d.polygon([(cx - r, y), (cx, y - r), (cx + r, y), (cx, y + r)], fill=color + (255,))
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS), 4


class Element:
    def __init__(self, img, baseline, cx, y, t_in, t_out, fade_in=0.8, fade_out=0.6, rise=14):
        self.b, self.cx, self.y = baseline, cx, y
        self.t_in, self.t_out, self.fi, self.fo, self.rise = t_in, t_out, fade_in, fade_out, rise
        self.arr = np.asarray(img).astype(np.float32) / 255.0

    def alpha_at(self, t):
        if t < self.t_in or t > self.t_out + self.fo:
            return 0.0, 0.0
        a = min(1.0, (t - self.t_in) / self.fi)
        e = 1 - (1 - a) ** 3
        if t > self.t_out:
            b = 1 - (t - self.t_out) / self.fo
            return e * b * b * (3 - 2 * b), (1 - e) * self.rise
        return e, (1 - e) * self.rise


def build_elements(T):
    els = []
    def add(txt, fnt, color, y, t_in, t_out, tracking=0.0, **kw):
        im, b = text_img(txt, fnt, color, tracking)
        els.append(Element(im, b, W / 2, y, t_in, t_out, **kw))
    def add_rule(width, y, t_in, t_out, **kw):
        im, b = rule_img(width)
        els.append(Element(im, b, W / 2, y, t_in, t_out, rise=0, **kw))

    title = font(F_SERIF, 92, 700)
    big_i = font(F_SERIF_I, 104, 500)
    mid_i = font(F_SERIF_I, 70, 500)
    caps = font(F_SANS, 30, 500)
    store = font(F_SERIF, 72, 600)
    addr = font(F_SANS, 34, 400)

    a, b = T['title']
    add_rule(150, 265, a, b)
    add('LETRAS', title, INK, 370, a + 0.15, b, tracking=0.20, fade_in=1.0)
    add('DECORATIVAS', title, INK, 475, a + 0.35, b, tracking=0.20, fade_in=1.0)
    a, b = T['artesanales']
    add('Artesanales', big_i, INK, 330, a, b, fade_in=0.9)
    add_rule(110, 380, a + 0.3, b)
    a, b = T['detalle']
    add('Un detalle único', mid_i, INK, 300, a, b)
    add('para tu hogar', mid_i, INK, 376, a + 0.2, b)
    a, b = T['stores']
    add('DISPONIBLES EN:', caps, INK2, 262, a, b, tracking=0.32)
    add_rule(120, 300, a + 0.25, b)
    s1 = T['store1']
    add('Mercería El Siglo', store, INK, 392, s1, b)
    add('C. Cortes de Aragón, 46', addr, INK2, 446, s1 + 0.25, b, tracking=0.05)
    s2 = T['store2']
    add('Papelería Casablanca', store, INK, 560, s2, b)
    add('C. La Vía, 16', addr, INK2, 614, s2 + 0.25, b, tracking=0.05)
    return els


def render(els, t):
    out = np.zeros((H, W, 4), np.float32)
    for e in els:
        a, dy = e.alpha_at(t)
        if a <= 0.001:
            continue
        h, w = e.arr.shape[:2]
        x0 = int(round(e.cx - w / 2)); y0 = int(round(e.y - e.b + dy))
        sa = e.arr[..., 3:4] * a
        reg = out[y0:y0 + h, x0:x0 + w]
        reg[..., :3] = e.arr[..., :3] * sa + reg[..., :3] * (1 - sa)
        reg[..., 3:4] = sa + reg[..., 3:4] * (1 - sa)
    return out
