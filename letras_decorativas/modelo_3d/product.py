"""3D turntable of the decorative letter. Geometry: real letter proportions (20 cm high, 4.5 cm deep)
built from the rectified outline; textures straight from the photographs (front = photo 1, floral
side = photo 3 with relief); pink sides / white inner walls sampled from the photos; satin pointe
shoes and organza ribbon modelled to match the photos. Renders only the product + its shadow
(transparent film, shadow catcher) with the same camera and lights as the rendered set."""
import bpy, bmesh, math, sys, os, json, time
from mathutils import Vector, Matrix, Euler

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from shape import OUTER, COUNTER, GAP, mirror

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
F0, F1 = int(args[0]), int(args[1])
SAMPLES = int(args[2]) if len(args) > 2 else 16
OUT = args[3] if len(args) > 3 else f'{D}/frames_prod'
RES_SCALE = float(args[4]) if len(args) > 4 else 1.0
TL = json.load(open(f'{D}/timeline.json'))

PX = 5925.0           # canonical px per metre (1185 px = 0.20 m)
T = 0.045             # letter depth (m)
CW, CH = 1120, 1325


def cx(x): return (x - 560) / PX
def cz(y): return (1255 - y) / PX


bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = SAMPLES
scn.cycles.use_adaptive_sampling = True
scn.cycles.adaptive_threshold = 0.04
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.cycles.denoising_prefilter = 'FAST'
try:
    scn.cycles.denoising_quality = 'FAST'
except Exception:
    pass
scn.cycles.max_bounces = 4
scn.cycles.transparent_max_bounces = 8
scn.render.film_transparent = True
scn.render.resolution_x, scn.render.resolution_y = 1080, 1920
scn.render.resolution_percentage = int(100 * RES_SCALE)
scn.render.use_persistent_data = True
if os.environ.get('THREADS'):
    scn.render.threads_mode = 'FIXED'; scn.render.threads = int(os.environ['THREADS'])
scn.view_settings.view_transform = 'Standard'
scn.view_settings.look = 'None'
scn.view_settings.exposure = 0.0
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
scn.render.image_settings.color_depth = '16'


def srgb(r, g, b):
    def c(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c(r), c(g), c(b), 1.0)


def mat_basic(name, col, rough=0.75, spec=0.25, sheen=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = col; b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    b.inputs['Sheen Weight'].default_value = sheen
    return m, b


def mat_image(name, path, alpha=False, rough=0.8, spec=0.2, gain=1.0, height=None, hscale=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(path)
    tex.interpolation = 'Cubic'; tex.extension = 'EXTEND'
    col = tex.outputs['Color']
    if gain != 1.0:
        mul = nt.nodes.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
        nt.links.new(col, mul.inputs[1]); mul.inputs[2].default_value = (gain, gain, gain, 1); col = mul.outputs[0]
    nt.links.new(col, b.inputs['Base Color'])
    if alpha:
        tex.image.alpha_mode = 'STRAIGHT'
        nt.links.new(tex.outputs['Alpha'], b.inputs['Alpha'])
    if height:
        ht = nt.nodes.new('ShaderNodeTexImage'); ht.image = bpy.data.images.load(height)
        ht.image.colorspace_settings.name = 'Non-Color'; ht.interpolation = 'Cubic'
        bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.6; bump.inputs['Distance'].default_value = hscale
        nt.links.new(ht.outputs['Color'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
    return m


# ---------------------------------------------------------------- the letter (solid)
outline = [OUTER[3], GAP[3], GAP[0], GAP[1], GAP[2], OUTER[2], OUTER[1], OUTER[0]]
cu = bpy.data.curves.new('letterA', 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
cu.extrude = T / 2 - 0.0012; cu.bevel_depth = 0.0012; cu.bevel_resolution = 2
for poly in (outline, COUNTER):
    sp = cu.splines.new('POLY'); sp.points.add(len(poly) - 1)
    for i, (x, y) in enumerate(poly):
        sp.points[i].co = (cx(x), cz(y), 0, 1)
    sp.use_cyclic_u = True
let = bpy.data.objects.new('letter', cu); scn.collection.objects.link(let)
bpy.context.view_layer.objects.active = let; let.select_set(True)
bpy.ops.object.convert(target='MESH')
let = bpy.context.active_object
let.rotation_euler = (math.radians(90), 0, 0)        # curve XY -> world XZ, extrusion along -Y/+Y
bpy.ops.object.transform_apply(rotation=True)

m_front = mat_image('front', f'{D}/tex_front.png', rough=0.7, spec=0.25)
m_backsolid = mat_image('backsolid', f'{D}/tex_back_opaque.png', rough=0.8)
m_pink, _ = mat_basic('pink', srgb(236, 196, 186), rough=0.7, spec=0.3)
m_white, _ = mat_basic('inner', srgb(240, 230, 222), rough=0.7, spec=0.25)
for mm in (m_front, m_backsolid, m_pink, m_white):
    let.data.materials.append(mm)


def near_poly(px, pz, poly, tol):
    x, y = px * PX + 560, 1255 - pz * PX
    best = 1e9
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L)) if L else 0
        best = min(best, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return best < tol


me = let.data
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
uv = me.uv_layers.new(name='UVMap'); me.uv_layers.active = uv; uv.active_render = True
for f in me.polygons:
    n = f.normal; c = f.center
    if n.y < -0.9:
        f.material_index = 0
    elif n.y > 0.9:
        f.material_index = 1
    else:
        inner = near_poly(c.x, c.z, COUNTER, 14) or (near_poly(c.x, c.z, GAP[:3], 14) and c.z > 0.001 and abs(c.x) < 0.02)
        f.material_index = 3 if inner else 2
    for li in f.loop_indices:
        v = me.vertices[me.loops[li].vertex_index].co
        xc = v.x * PX + 560; yc = 1255 - v.z * PX
        if f.material_index == 1:            # back face seen from behind: mirrored canonical
            xc = 2 * 560 - xc
        uv.data[li].uv = (xc / CW, 1 - yc / CH)

# ---------------------------------------------------------------- floral layer with relief (back)
m_flow = mat_image('flowers', f'{D}/tex_back.png', alpha=True, rough=0.85, spec=0.15,
                   height=f'{D}/tex_back_h.png', hscale=0.002)
m_flow.node_tree.nodes['Principled BSDF'].inputs['Subsurface Weight'].default_value = 0.08
bpy.ops.mesh.primitive_grid_add(x_subdivisions=280, y_subdivisions=330, size=1)
fl = bpy.context.active_object; fl.name = 'flowers'
fl.data.materials.append(m_flow)
w_m, h_m = CW / PX, CH / PX
for v in fl.data.vertices:          # grid in XY -> place in XZ, facing +Y (back)
    u, t = v.co.x + 0.5, v.co.y + 0.5
    xc_back = u * CW; yc = (1 - t) * CH
    xc = 2 * 560 - xc_back
    v.co = Vector((cx(xc), T / 2 + 0.0008, cz(yc)))
fuv = fl.data.uv_layers.active
for loop in fl.data.loops:
    v = fl.data.vertices[loop.vertex_index].co
    xc = v.x * PX + 560; yc = 1255 - v.z * PX
    fuv.data[loop.index].uv = ((2 * 560 - xc) / CW, 1 - yc / CH)
for p in fl.data.polygons: p.use_smooth = True
himg = bpy.data.images.load(f'{D}/tex_back_h.png'); himg.colorspace_settings.name = 'Non-Color'
htex = bpy.data.textures.new('relief', 'IMAGE'); htex.image = himg; htex.extension = 'EXTEND'
dm = fl.modifiers.new('relief', 'DISPLACE'); dm.texture = htex; dm.texture_coords = 'UV'
dm.direction = 'Y'; dm.strength = 0.007; dm.mid_level = 0.0

# ---------------------------------------------------------------- pointe shoes (satin)
satin = bpy.data.materials.new('satin'); satin.use_nodes = True
sb = satin.node_tree.nodes['Principled BSDF']
sb.inputs['Base Color'].default_value = srgb(246, 234, 230)
sb.inputs['Roughness'].default_value = 0.22
sb.inputs['Anisotropic'].default_value = 0.6
sb.inputs['Sheen Weight'].default_value = 1.0; sb.inputs['Sheen Tint'].default_value = srgb(255, 226, 232); sb.inputs['Sheen Roughness'].default_value = 0.3
sb.inputs['Coat Weight'].default_value = 0.6; sb.inputs['Coat Roughness'].default_value = 0.08
try:
    sb.inputs['Thin Film Thickness'].default_value = 320; sb.inputs['Thin Film IOR'].default_value = 1.35
except KeyError:
    pass
inner_satin, ib = mat_basic('satin_in', srgb(236, 214, 210), rough=0.5, spec=0.4, sheen=0.6)


def make_shoe(name, L=0.084, W=0.036, Hh=0.031):
    """satin pointe shoe: full rounded slipper, toe box ending in a small flat platform,
    heel rounded, opening (vamp) on the upper side of the heel half."""
    bm = bmesh.new(); NU, NV = 56, 40; rings = []
    for i in range(NU + 1):
        u = i / NU                                   # 0 = heel, 1 = toe
        x = (u - 0.5) * L
        heel = math.sqrt(max(0.0, 1 - ((0.22 - u) / 0.22) ** 2)) if u < 0.22 else 1.0
        tip = math.sqrt(max(0.0, 1 - ((u - 0.80) / 0.20) ** 2)) if u > 0.80 else 1.0
        toe = 1.0 if u < 0.40 else (1 - 0.30 * ((u - 0.40) / 0.60) ** 1.3)  # gentle taper of the box
        w = W / 2 * heel * toe * max(tip, 0.0); h = Hh / 2 * heel * max(tip, 0.0) * (0.88 + 0.12 * toe)
        if u > 0.97:                                 # small flat platform
            w = max(w, W * 0.16); h = max(h, Hh * 0.16)
        ring = []
        for j in range(NV):
            a = 2 * math.pi * j / NV
            y = w * math.cos(a); z = h * math.sin(a) * (1.0 if math.sin(a) > 0 else 0.75)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for i in range(NU):
        for j in range(NV):
            a, b = rings[i][j], rings[i][(j + 1) % NV]
            c, d = rings[i + 1][(j + 1) % NV], rings[i + 1][j]
            mid_u = (i + 0.5) / NU; ang = 2 * math.pi * (j + 0.5) / NV
            if 0.12 < mid_u < 0.46 and math.sin(ang) > 0.62 - 0.35 * (mid_u - 0.12):  # vamp opening
                continue
            bm.faces.new((a, b, c, d))
    bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=rings[0], dist=1e-4)
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    ob = bpy.data.objects.new(name, mesh); scn.collection.objects.link(ob)
    for p in mesh.polygons: p.use_smooth = True
    ob.data.materials.append(satin); ob.data.materials.append(inner_satin)
    sol = ob.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.0015; sol.material_offset = 1
    ob.modifiers.new('sub', 'SUBSURF').levels = 1
    return ob


def place(ob, loc, toe_dir, open_dir):
    t = Vector(toe_dir).normalized(); o = Vector(open_dir); o = (o - t * o.dot(t)).normalized(); s = o.cross(t)
    M = Matrix((t, s, o)).transposed()          # local x->toe, y->side, z->opening
    ob.matrix_world = Matrix.Translation(loc) @ M.to_4x4()


shoe1 = make_shoe('shoe_upper'); place(shoe1, Vector((-0.0760, 0.004, 0.170)), (-0.55, 1.0, -0.22), (-0.45, -0.05, 1.0))
shoe2 = make_shoe('shoe_lower'); place(shoe2, Vector((-0.0840, 0.008, 0.122)), (-0.40, 1.0, -0.40), (-0.70, -0.05, 0.80))

# ---------------------------------------------------------------- organza ribbon
org = bpy.data.materials.new('organza'); org.use_nodes = True
ob_ = org.node_tree.nodes['Principled BSDF']
ob_.inputs['Base Color'].default_value = srgb(150, 62, 80)
ob_.inputs['Roughness'].default_value = 0.35; ob_.inputs['Alpha'].default_value = 0.40
ob_.inputs['Sheen Weight'].default_value = 0.8; ob_.inputs['Sheen Tint'].default_value = srgb(240, 190, 200)
ob_.inputs['Specular IOR Level'].default_value = 0.5


def catmull(pts, n=16):
    P = [Vector(p) for p in pts]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2]); return out


def ribbon(name, pts, width=0.012, up=(0, 1, 0), twist=0.0):
    path = catmull(pts); bm = bmesh.new(); prev = None; U = Vector(up).normalized()
    for i, p in enumerate(path):
        tng = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = tng.cross(U)
        if side.length < 1e-4: side = tng.cross(Vector((1, 0, 0)))
        side.normalize()
        if twist: side = Matrix.Rotation(twist * i / len(path), 3, tng) @ side
        a = bm.verts.new(p + side * width / 2); b = bm.verts.new(p - side * width / 2)
        if prev: bm.faces.new((prev[0], prev[1], b, a))
        prev = (a, b)
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    ob = bpy.data.objects.new(name, mesh); scn.collection.objects.link(ob); ob.data.materials.append(org)
    for p in mesh.polygons: p.use_smooth = True
    ob.modifiers.new('sol', 'SOLIDIFY').thickness = 0.0004
    return ob


BOW = Vector((-0.089, -0.012, 0.183))
rib = [
    ribbon('arc', [(-0.074, 0.010, 0.186), (-0.060, 0.012, 0.212), (-0.030, 0.012, 0.226), (0.000, 0.010, 0.219), (0.025, 0.008, 0.2035), (0.040, 0.006, 0.2008)], 0.010, up=(0, 1, 0)),
    ribbon('loop1', [BOW, BOW + Vector((-0.010, -0.010, 0.016)), BOW + Vector((-0.020, -0.002, 0.020)), BOW + Vector((-0.018, 0.004, 0.006)), BOW], 0.011, up=(1, 0, 0)),
    ribbon('loop2', [BOW, BOW + Vector((0.004, -0.014, 0.018)), BOW + Vector((0.014, -0.010, 0.024)), BOW + Vector((0.010, -0.002, 0.008)), BOW], 0.011, up=(1, 0, 0)),
    ribbon('tail1', [BOW, BOW + Vector((-0.014, -0.006, -0.018)), BOW + Vector((-0.022, -0.004, -0.045)), BOW + Vector((-0.020, 0.000, -0.072))], 0.011, up=(1, 0, 0), twist=0.9),
    ribbon('tail2', [BOW, BOW + Vector((-0.004, 0.008, -0.022)), BOW + Vector((-0.010, 0.016, -0.052)), BOW + Vector((-0.006, 0.022, -0.085))], 0.011, up=(1, 0, 0), twist=-0.7),
    ribbon('wrap', [(-0.056, -0.020, 0.150), (-0.070, -0.026, 0.162), (-0.088, -0.018, 0.180), (-0.090, 0.004, 0.186), (-0.074, 0.016, 0.182), (-0.056, 0.020, 0.170)], 0.012, up=(1, 0, 0)),
]
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0045, location=BOW); knot = bpy.context.active_object; knot.data.materials.append(org)

# ---------------------------------------------------------------- turntable parent
pivot = bpy.data.objects.new('turntable', None); scn.collection.objects.link(pivot)
for ob in [let, fl, shoe1, shoe2, knot] + rib:
    ob.parent = pivot

# ---------------------------------------------------------------- shadow catcher, lights (same as the set)
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 0))
catcher = bpy.context.active_object; catcher.is_shadow_catcher = True
world = bpy.data.worlds.new('w'); scn.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(238, 222, 210)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = float(os.environ.get('WORLD_E', '0.6'))


def area(loc, size, sy, energy, col, target=(0, 0, 0.1)):
    bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.active_object
    L.data.shape = 'RECTANGLE'; L.data.size = size; L.data.size_y = sy; L.data.energy = energy; L.data.color = col
    L.rotation_mode = 'QUATERNION'; L.rotation_quaternion = Vector((0, 0, -1)).rotation_difference((Vector(target) - L.location).normalized())
    return L
KEY_E = float(os.environ.get('KEY_E', '32'))
area((-1.0, -0.9, 0.9), 1.4, 1.8, KEY_E, (1.0, 0.92, 0.84))
area((1.0, -0.7, 0.45), 1.2, 1.2, KEY_E * 0.33, (1.0, 0.94, 0.90))
area((0.4, 1.0, 0.8), 1.0, 1.0, KEY_E * 0.35, (1.0, 0.90, 0.80))     # warm rim from the window side

# ---------------------------------------------------------------- camera (identical to the set, plus the virtual dolly)
DIST, ELEV, LENS = 1.25, math.radians(14), 88.0
AIM = Vector((0, 0, 0.165))
cam_loc = Vector((0, 0, 0.10)) + Vector((0, -math.cos(ELEV), math.sin(ELEV))) * DIST
bpy.ops.object.camera_add(location=cam_loc); cam = bpy.context.active_object
cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (AIM - cam_loc).to_track_quat('-Z', 'Y')
cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 36; cam.data.lens = LENS
scn.camera = cam


def smooth_keys(keys, t):
    ts = [k[0] for k in keys]
    if t <= ts[0]: return list(keys[0][1:])
    if t >= ts[-1]: return list(keys[-1][1:])
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    P = [k[1:] for k in keys]; t0, t1 = ts[i], ts[i + 1]; h = t1 - t0; u = (t - t0) / h

    def tan(j):
        if j == 0 or j == len(ts) - 1: return [0.0] * len(P[j])
        return [(P[j + 1][d] - P[j - 1][d]) / (ts[j + 1] - ts[j - 1]) * 0.85 for d in range(len(P[j]))]
    m0, m1 = tan(i), tan(i + 1)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return [h00 * P[i][d] + h10 * m0[d] * h + h01 * P[i + 1][d] + h11 * m1[d] * h for d in range(len(P[i]))]


def set_camera(t):
    Z, Cx, Cy = smooth_keys(TL['cam'], t)
    cam.data.lens = LENS * Z
    # zoom about C (screen px of the zoom-1 frame): shift is a fraction of the larger image side (1920)
    cam.data.shift_x = Z * (Cx - 540.0) / 1920.0
    cam.data.shift_y = -Z * (Cy - 960.0) / 1920.0


def set_border():
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    xs, ys = [], []
    for x in (-0.13, 0.13):
        for y in (-0.13, 0.13):
            for z in (-0.005, 0.24):
                c = world_to_camera_view(scn, cam, Vector((x, y, z))); xs.append(c.x); ys.append(c.y)
    pad = 0.02
    scn.render.use_border = True; scn.render.use_crop_to_border = False
    scn.render.border_min_x = max(0, min(xs) - pad); scn.render.border_max_x = min(1, max(xs) + pad)
    scn.render.border_min_y = max(0, min(ys) - 0.06); scn.render.border_max_y = min(1, max(ys) + pad)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    phi = TL['phi']           # degrees per frame
    for k in range(F0, F1):
        fn = f'{OUT}/{k:04d}.png'
        if os.path.exists(fn): continue
        t0 = time.time(); t = k / TL['fps']
        pivot.rotation_euler = (0, 0, math.radians(phi[k]))
        set_camera(t)
        set_border()
        scn.render.filepath = fn
        bpy.ops.render.render(write_still=True)
        print('FRAME', k, round(time.time() - t0, 1), flush=True)
