"""Elegant on-screen typography for the 1080x1920 spot."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, os
D = os.path.dirname(os.path.abspath(__file__))
F_SERIF = f'{D}/fonts/CormorantGaramond%5Bwght%5D.ttf'
F_SERIF_I = f'{D}/fonts/CormorantGaramond-Italic%5Bwght%5D.ttf'
F_SANS = f'{D}/fonts/Montserrat%5Bwght%5D.ttf'
W, H = 1080, 1920
SS = 2  # supersampling for crisp antialiasing

INK = (58, 42, 31)
INK2 = (107, 86, 70)
RULE = (168, 139, 96)


def font(path, size, wght):
    f = ImageFont.truetype(path, size * SS)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def text_img(txt, fnt, color, tracking=0.0):
    """Render text to a tight RGBA image (at final scale). tracking in em."""
    size = fnt.size
    asc, desc = fnt.getmetrics()
    if tracking:
        widths = [fnt.getlength(c) for c in txt]
        total = sum(widths) + tracking * size * (len(txt) - 1)
    else:
        total = fnt.getlength(txt)
    pad = 8 * SS
    im = Image.new('RGBA', (int(total) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad
        for c, w in zip(txt, widths):
            d.text((x, pad), c, font=fnt, fill=color + (255,))
            x += w + tracking * size
    else:
        d.text((pad, pad), txt, font=fnt, fill=color + (255,))
    im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    return im, (asc + pad) / SS  # image, baseline offset from top


def rule_img(width, color=RULE, thick=1.6):
    im = Image.new('RGBA', (int(width * SS), int(6 * SS)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 3 * SS
    d.rectangle([0, y - thick * SS / 2, width * SS, y + thick * SS / 2], fill=color + (255,))
    # tiny lozenge in the middle
    cx = width * SS / 2; r = 3.2 * SS
    d.polygon([(cx - r, y), (cx, y - r), (cx + r, y), (cx, y + r)], fill=color + (255,))
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS), 3


class Element:
    def __init__(self, img, baseline, cx, y, t_in, t_out, fade_in=0.8, fade_out=0.55, rise=16):
        self.img, self.b = img, baseline
        self.cx, self.y = cx, y
        self.t_in, self.t_out, self.fi, self.fo, self.rise = t_in, t_out, fade_in, fade_out, rise
        self.arr = np.asarray(img).astype(np.float32) / 255.0

    def alpha_at(self, t):
        if t < self.t_in or t > self.t_out + self.fo:
            return 0.0, 0.0
        a = min(1.0, (t - self.t_in) / self.fi)
        e = 1 - (1 - a) ** 3  # ease-out
        if t > self.t_out:
            b = 1 - (t - self.t_out) / self.fo
            e_out = b * b * (3 - 2 * b)
            return e * e_out, (1 - e) * self.rise
        return e, (1 - e) * self.rise


def build_elements(T):
    """T: dict of timings."""
    els = []
    def add(txt, fnt, color, y, t_in, t_out, tracking=0.0, **kw):
        im, b = text_img(txt, fnt, color, tracking)
        els.append(Element(im, b, W / 2, y, t_in, t_out, **kw))
    def add_rule(width, y, t_in, t_out, **kw):
        im, b = rule_img(width)
        els.append(Element(im, b, W / 2, y, t_in, t_out, rise=0, **kw))

    caps = font(F_SANS, 29, 450)
    caps_s = font(F_SANS, 26, 500)
    addr = font(F_SANS, 34, 400)
    serif_i_big = font(F_SERIF_I, 118, 500)
    serif_i_mid = font(F_SERIF_I, 66, 500)
    serif_store = font(F_SERIF, 74, 600)
    serif_name = font(F_SERIF, 64, 600)
    serif_i_end = font(F_SERIF_I, 92, 500)

    # 1) title
    a, b = T['title']
    add('AMBIENTADORES', caps, INK2, 318, a, b, tracking=0.42)
    add('del Cachirulo', serif_i_big, INK, 438, a + 0.25, b, fade_in=1.0)
    add_rule(120, 488, a + 0.6, b)
    # 2) craft + spray
    a, b = T['craft']
    add('Elaborados de forma artesanal', serif_i_mid, INK, 360, a, b)
    add_rule(90, 408, a + 0.3, b)
    a2 = T['spray']
    add('CON PULVERIZADOR DE 10 ML INCLUIDO', caps, INK2, 466, a2, b, tracking=0.22)
    # 3) stores
    a, b = T['excl']
    add('DISPONIBLE EXCLUSIVAMENTE EN', caps_s, INK2, 232, a, b, tracking=0.30)
    add('TIENDAS COLABORADORAS', caps_s, INK2, 272, a + 0.12, b, tracking=0.30)
    add_rule(90, 312, a + 0.4, b)
    s1 = T['store1']
    add('Mercería El Siglo', serif_store, INK, 400, s1, b)
    add('C. Cortes de Aragón 46', addr, INK2, 455, s1 + 0.25, b, tracking=0.06)
    s2 = T['store2']
    add('Papelería Casablanca', serif_store, INK, 548, s2, b)
    add('C. La Vía 16', addr, INK2, 606, s2 + 0.25, b, tracking=0.06)
    # 4) closing
    a, b = T['end']
    add('Descubre los', serif_i_mid, INK2, 300, a, b)
    add('Ambientadores del Cachirulo', serif_name, INK, 378, a + 0.2, b)
    add_rule(110, 426, a + 0.5, b)
    add('Te esperamos', serif_i_end, INK, 520, T['wait'], b, fade_in=1.0)
    return els


def render(els, t, canvas=None):
    """Return premultiplied-ready RGBA float array HxWx4 for time t."""
    out = np.zeros((H, W, 4), np.float32) if canvas is None else canvas
    for e in els:
        a, dy = e.alpha_at(t)
        if a <= 0.001:
            continue
        h, w = e.arr.shape[:2]
        x0 = int(round(e.cx - w / 2))
        y0 = int(round(e.y - e.b + dy))
        src = e.arr
        sa = src[..., 3:4] * a
        region = out[y0:y0 + h, x0:x0 + w]
        region[..., :3] = src[..., :3] * sa + region[..., :3] * (1 - sa)
        region[..., 3:4] = sa + region[..., 3:4] * (1 - sa)
    return out
