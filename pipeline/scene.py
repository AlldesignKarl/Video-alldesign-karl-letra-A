import bpy, math, sys, random
from mathutils import Vector, Euler

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RES_X = int(args[0]) if len(args) > 0 else 324
RES_Y = int(args[1]) if len(args) > 1 else 576
SAMPLES = int(args[2]) if len(args) > 2 else 32
OUT = args[3] if len(args) > 3 else '/tmp/bg.png'
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.render.resolution_x = RES_X
scn.render.resolution_y = RES_Y
scn.render.film_transparent = False
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'
scn.view_settings.exposure = -1.1
scn.cycles.max_bounces = 8
scn.cycles.blur_glossy = 0.5


def srgb(r, g, b):
    def c(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c(r), c(g), c(b), 1.0)


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    return m, nt, bsdf


def add_box(name, size, loc, rot=(0, 0, 0), mat=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = 4
    if mat: o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------- materials
# warm lime-plaster wall
wall_m, nt, b = new_mat('wall')
tc = nt.nodes.new('ShaderNodeTexCoord')
n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 6; n1.inputs['Detail'].default_value = 8; n1.inputs['Roughness'].default_value = 0.6
n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 60; n2.inputs['Detail'].default_value = 4
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = srgb(226, 214, 196)
ramp.color_ramp.elements[1].color = srgb(240, 232, 218)
nt.links.new(tc.outputs['Object'], n1.inputs['Vector'])
nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; bump.inputs['Distance'].default_value = 0.004
nt.links.new(n2.outputs['Fac'], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
b.inputs['Roughness'].default_value = 0.92

# natural linen tablecloth
lin_m, nt, b = new_mat('linen')
tc = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 1)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
wx = nt.nodes.new('ShaderNodeTexWave'); wx.wave_type = 'BANDS'; wx.bands_direction = 'X'; wx.inputs['Scale'].default_value = 900; wx.inputs['Distortion'].default_value = 2.5; wx.inputs['Detail'].default_value = 2
wy = nt.nodes.new('ShaderNodeTexWave'); wy.wave_type = 'BANDS'; wy.bands_direction = 'Y'; wy.inputs['Scale'].default_value = 900; wy.inputs['Distortion'].default_value = 2.5; wy.inputs['Detail'].default_value = 2
nt.links.new(mp.outputs['Vector'], wx.inputs['Vector']); nt.links.new(mp.outputs['Vector'], wy.inputs['Vector'])
mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
nt.links.new(wx.outputs['Fac'], mx.inputs[0]); nt.links.new(wy.outputs['Fac'], mx.inputs[1])
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14; nz.inputs['Detail'].default_value = 6
nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = srgb(214, 200, 178)
ramp.color_ramp.elements[1].color = srgb(234, 224, 206)
mixf = nt.nodes.new('ShaderNodeMath'); mixf.operation = 'MULTIPLY_ADD'
mixf.inputs[1].default_value = 0.35
nt.links.new(mx.outputs[0], mixf.inputs[0]); nt.links.new(nz.outputs['Fac'], mixf.inputs[2])
nt.links.new(mixf.outputs[0], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.0008
nt.links.new(mx.outputs[0], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
b.inputs['Roughness'].default_value = 0.95
b.inputs['Sheen Weight'].default_value = 0.4
b.inputs['Sheen Tint'].default_value = srgb(250, 240, 225)

# travertine plinth
trav_m, nt, b = new_mat('travertine')
tc = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 9)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 3; n1.inputs['Detail'].default_value = 10; n1.inputs['Distortion'].default_value = 0.4
nt.links.new(mp.outputs['Vector'], n1.inputs['Vector'])
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = srgb(192, 170, 140)
ramp.color_ramp.elements[1].color = srgb(226, 210, 186)
nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 160
nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
pits = nt.nodes.new('ShaderNodeMath'); pits.operation = 'LESS_THAN'; pits.inputs[1].default_value = 0.06
nt.links.new(vor.outputs['Distance'], pits.inputs[0])
dark = nt.nodes.new('ShaderNodeMix'); dark.data_type = 'RGBA'; dark.blend_type = 'MULTIPLY'
nt.links.new(pits.outputs[0], dark.inputs['Factor'])
nt.links.new(ramp.outputs['Color'], dark.inputs[6])
dark.inputs[7].default_value = srgb(175, 160, 140)
nt.links.new(dark.outputs[2], b.inputs['Base Color'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.6; bump.inputs['Distance'].default_value = 0.0015
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
nt.links.new(pits.outputs[0], inv.inputs[1])
nt.links.new(inv.outputs[0], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
b.inputs['Roughness'].default_value = 0.55

# Muel-style tin-glazed ceramic: cream glaze, cobalt hand-painted motifs on the belly
cer_m, nt, b = new_mat('ceramic')
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
# belly band mask: |z| < 0.45 (object space, sphere radius 1 after scale applied? use generated)
gen_sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Generated'], gen_sep.inputs['Vector'])
lo = nt.nodes.new('ShaderNodeMath'); lo.operation = 'GREATER_THAN'; lo.inputs[1].default_value = 0.36
hi = nt.nodes.new('ShaderNodeMath'); hi.operation = 'LESS_THAN'; hi.inputs[1].default_value = 0.66
nt.links.new(gen_sep.outputs['Z'], lo.inputs[0]); nt.links.new(gen_sep.outputs['Z'], hi.inputs[0])
bandm = nt.nodes.new('ShaderNodeMath'); bandm.operation = 'MULTIPLY'
nt.links.new(lo.outputs[0], bandm.inputs[0]); nt.links.new(hi.outputs[0], bandm.inputs[1])
mot = nt.nodes.new('ShaderNodeTexVoronoi'); mot.feature = 'SMOOTH_F1'; mot.inputs['Scale'].default_value = 9
nt.links.new(tc.outputs['Generated'], mot.inputs['Vector'])
mt = nt.nodes.new('ShaderNodeMath'); mt.operation = 'LESS_THAN'; mt.inputs[1].default_value = 0.22
nt.links.new(mot.outputs['Distance'], mt.inputs[0])
m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'
nt.links.new(mt.outputs[0], m2.inputs[0]); nt.links.new(bandm.outputs[0], m2.inputs[1])
# thin rim lines
ln1 = nt.nodes.new('ShaderNodeMath'); ln1.operation = 'COMPARE'; ln1.inputs[1].default_value = 0.34; ln1.inputs[2].default_value = 0.008
ln2 = nt.nodes.new('ShaderNodeMath'); ln2.operation = 'COMPARE'; ln2.inputs[1].default_value = 0.68; ln2.inputs[2].default_value = 0.008
nt.links.new(gen_sep.outputs['Z'], ln1.inputs[0]); nt.links.new(gen_sep.outputs['Z'], ln2.inputs[0])
a1 = nt.nodes.new('ShaderNodeMath'); a1.operation = 'MAXIMUM'
nt.links.new(ln1.outputs[0], a1.inputs[0]); nt.links.new(ln2.outputs[0], a1.inputs[1])
a2 = nt.nodes.new('ShaderNodeMath'); a2.operation = 'MAXIMUM'
nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(m2.outputs[0], a2.inputs[1])
mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'
nt.links.new(a2.outputs[0], mixc.inputs['Factor'])
mixc.inputs[6].default_value = srgb(240, 233, 216)
mixc.inputs[7].default_value = srgb(52, 82, 138)
nt.links.new(mixc.outputs[2], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.12
b.inputs['Coat Weight'].default_value = 0.6

# terracotta (base of jug, small dish)
terr_m, nt, b = new_mat('terracotta')
b.inputs['Base Color'].default_value = srgb(176, 108, 74)
b.inputs['Roughness'].default_value = 0.8

# dried wheat
wheat_m, nt, b = new_mat('wheat')
b.inputs['Base Color'].default_value = srgb(214, 182, 128)
b.inputs['Roughness'].default_value = 0.7
b.inputs['Subsurface Weight'].default_value = 0.15

# cachirulo: red/black check with thin light lines
cach_m, nt, b = new_mat('cachirulo')
tc = nt.nodes.new('ShaderNodeTexCoord')
chk = nt.nodes.new('ShaderNodeTexChecker'); chk.inputs['Scale'].default_value = 34
chk.inputs['Color1'].default_value = srgb(150, 28, 34)
chk.inputs['Color2'].default_value = srgb(28, 22, 22)
nt.links.new(tc.outputs['UV'], chk.inputs['Vector'])
nt.links.new(chk.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.8
b.inputs['Sheen Weight'].default_value = 0.5

# leaf (shadow caster only)
leaf_m, nt, b = new_mat('leaf')
b.inputs['Base Color'].default_value = srgb(90, 100, 70)

# light oak (stool under jug / tray)
oak_m, nt, b = new_mat('oak')
tc = nt.nodes.new('ShaderNodeTexCoord')
wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 3; wv.inputs['Distortion'].default_value = 8; wv.inputs['Detail'].default_value = 3
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 12, 1)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = srgb(176, 140, 100)
ramp.color_ramp.elements[1].color = srgb(204, 172, 130)
nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.6

# ---------------------------------------------------------------- geometry
TABLE_Z = -0.075
WALL_Y = 0.62

# wall + table (large planes)
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, WALL_Y, 1.0), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object; wall.data.materials.append(wall_m)
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, WALL_Y - 3, TABLE_Z))
table = bpy.context.active_object; table.data.materials.append(lin_m)

# gentle cove where cloth meets wall: soft linen fold along the back
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=4, location=(0, WALL_Y - 0.02, TABLE_Z + 0.005), rotation=(0, math.radians(90), 0))
fold = bpy.context.active_object; fold.data.materials.append(lin_m); fold.scale = (1, 1, 1)

# travertine plinth (the product sits on top at z=0)
bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=0.118, depth=0.075, location=(0, 0, -0.0375))
pl = bpy.context.active_object; pl.name = 'plinth'
bv = pl.modifiers.new('bev', 'BEVEL'); bv.width = 0.004; bv.segments = 5
pl.data.materials.append(trav_m)
bpy.ops.object.shade_smooth()

# Muel jug with dried wheat, back right
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.085, location=(0.215, 0.40, TABLE_Z + 0.09))
jug = bpy.context.active_object; jug.scale = (1, 1, 1.25); jug.data.materials.append(cer_m); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.035, depth=0.09, location=(0.215, 0.40, TABLE_Z + 0.22))
neck = bpy.context.active_object; neck.data.materials.append(cer_m); bpy.ops.object.shade_smooth()
for i in range(22):
    ang = random.uniform(-0.55, 0.45); ang2 = random.uniform(-0.4, 0.4)
    L = random.uniform(0.20, 0.27)
    base = Vector((0.215, 0.40, TABLE_Z + 0.22))
    d = Vector((math.sin(ang), math.sin(ang2) * 0.5, math.cos(ang))).normalized()
    mid = base + d * L / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0018, depth=L, location=mid)
    st = bpy.context.active_object
    st.rotation_mode = 'QUATERNION'; st.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    st.data.materials.append(wheat_m)
    tip = base + d * (L + 0.03)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=8, radius=0.012, location=tip)
    hd = bpy.context.active_object
    hd.rotation_mode = 'QUATERNION'; hd.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    hd.scale = (0.8, 0.8, 3.0)
    hd.data.materials.append(wheat_m)

# small terracotta dish in front of the jug
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.07, depth=0.018, location=(0.25, 0.20, TABLE_Z + 0.009))
dish = bpy.context.active_object; dish.data.materials.append(terr_m)
bv = dish.modifiers.new('bev', 'BEVEL'); bv.width = 0.006; bv.segments = 4
bpy.ops.object.shade_smooth()

# folded cachirulo, back left (stack of softly bevelled folds)
for k in range(3):
    o = add_box(f'cach{k}', (0.20 - k * 0.004, 0.13 - k * 0.003, 0.009), (-0.235 + k * 0.002, 0.27, TABLE_Z + 0.0045 + k * 0.0088), rot=(0, 0, math.radians(-14)), mat=cach_m, bevel=0.0042)
    bpy.ops.object.shade_smooth()
# wooden board under it
add_box('board', (0.26, 0.17, 0.016), (-0.235, 0.27, TABLE_Z), rot=(0, 0, math.radians(-14)), mat=oak_m, bevel=0.003)
for k in range(3):
    o = bpy.data.objects[f'cach{k}']; o.location.z += 0.008

# ---------------------------------------------------------------- lights
world = bpy.data.worlds.new('w'); scn.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = srgb(235, 224, 205)
bg.inputs['Strength'].default_value = 0.22

# afternoon sun through a window (left), falling on the back wall
sun_dir = Vector((0.78, 0.55, -0.30)).normalized()
bpy.ops.object.light_add(type='SUN', location=(0, 0, 2))
sun = bpy.context.active_object
sun.data.energy = 3.4
sun.data.angle = math.radians(1.6)
sun.data.color = (1.0, 0.76, 0.52)
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(sun_dir)

# window frame occluder built in a plane perpendicular to the sun, left of frame
wc = Vector((0.02, 0.62, 0.20)) - sun_dir * 1.4   # window centre in space
u = sun_dir.cross(Vector((0, 0, 1))).normalized()   # horizontal axis of window plane
v = u.cross(sun_dir).normalized()                    # vertical axis
quat = Vector((0, 0, 1)).rotation_difference(sun_dir)


def occluder(cu, cv, su, sv):
    loc = wc + u * cu + v * cv
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object
    o.rotation_mode = 'QUATERNION'
    # align plane: local x->u, local y->v
    from mathutils import Matrix
    M = Matrix((u, v, -sun_dir)).transposed()
    o.rotation_quaternion = M.to_quaternion()
    o.scale = (su, sv, 1)
    o.data.materials.append(leaf_m)
    o.visible_camera = False
    o.visible_glossy = False
    o.visible_diffuse = False
    return o

W, H = 0.62, 0.95  # window opening
occluder(0, H / 2 + 1.5, 6, 3)          # top wall
occluder(0, -H / 2 - 1.5, 6, 3)         # bottom wall
occluder(-W / 2 - 1.5, 0, 3, 6)         # left
occluder(W / 2 + 1.5, 0, 3, 6)          # right
occluder(0, 0.08, W, 0.035)             # transom
occluder(0, 0, 0.035, H)                # mullion

# olive branch shadow caster, between window and wall
from mathutils import Matrix
olive_c = wc + sun_dir * 0.55 + u * 0.10 + v * 0.22
for br in range(3):
    p = olive_c + u * random.uniform(-0.15, 0.15) + v * random.uniform(-0.1, 0.1)
    dirv = (u * random.uniform(-1, 1) + v * random.uniform(-0.6, 0.2)).normalized()
    for i in range(22):
        p = p + dirv * 0.018
        dirv = (dirv + (u * random.uniform(-0.25, 0.25) + v * random.uniform(-0.25, 0.25))).normalized()
        side = 1 if i % 2 == 0 else -1
        leafdir = (dirv + (u.cross(sun_dir) if side > 0 else -u.cross(sun_dir)) * 0 + (u if side > 0 else -u) * 0.8).normalized()
        bpy.ops.mesh.primitive_plane_add(size=1, location=p + leafdir * 0.03)
        lf = bpy.context.active_object
        a = math.atan2(leafdir.dot(v), leafdir.dot(u))
        M = Matrix((u, v, -sun_dir)).transposed()
        lf.rotation_mode = 'QUATERNION'
        lf.rotation_quaternion = M.to_quaternion() @ Euler((random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4), a)).to_quaternion()
        lf.scale = (0.062, 0.012, 1)
        lf.data.materials.append(leaf_m)
        lf.visible_camera = False; lf.visible_glossy = False; lf.visible_diffuse = False

# soft window fill (big area light, front-left) for the plinth / product zone
bpy.ops.object.light_add(type='AREA', location=(-0.9, -0.7, 0.75))
key = bpy.context.active_object
key.data.shape = 'RECTANGLE'; key.data.size = 1.2; key.data.size_y = 1.6
key.data.energy = 60
key.data.color = (1.0, 0.92, 0.82)
key.rotation_mode = 'QUATERNION'
key.rotation_quaternion = Vector((0, 0, -1)).rotation_difference((Vector((0, 0.05, 0.05)) - key.location).normalized())

# subtle bounce from the right
bpy.ops.object.light_add(type='AREA', location=(0.9, -0.6, 0.35))
fill = bpy.context.active_object
fill.data.size = 1.0; fill.data.energy = 12; fill.data.color = (1.0, 0.95, 0.88)
fill.rotation_mode = 'QUATERNION'
fill.rotation_quaternion = Vector((0, 0, -1)).rotation_difference((Vector((0, 0, 0.05)) - fill.location).normalized())

# ---------------------------------------------------------------- camera
TARGET = Vector((0, 0, 0.135))
DIST = 1.10
ELEV = math.radians(17)
cam_loc = TARGET + Vector((0, -math.cos(ELEV), math.sin(ELEV))) * DIST
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.active_object
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (TARGET - cam_loc).to_track_quat('-Z', 'Y')
cam.data.sensor_fit = 'HORIZONTAL'
cam.data.sensor_width = 36
cam.data.lens = 116
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (Vector((0, 0, 0.05)) - cam_loc).length
cam.data.dof.aperture_fstop = 2.8
cam.data.dof.aperture_blades = 9
scn.camera = cam

# passes for compositing (depth)
vl = scn.view_layers[0]
vl.use_pass_z = True
DEPTH = len(args) > 4 and args[4] == 'depth'
if DEPTH:
    dm = bpy.data.materials.new('depthmat'); dm.use_nodes = True
    ntd = dm.node_tree
    for nd in list(ntd.nodes): ntd.nodes.remove(nd)
    camd = ntd.nodes.new('ShaderNodeCameraData')
    mul = ntd.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.1
    em = ntd.nodes.new('ShaderNodeEmission')
    outn = ntd.nodes.new('ShaderNodeOutputMaterial')
    ntd.links.new(camd.outputs['View Z Depth'], mul.inputs[0])
    ntd.links.new(mul.outputs[0], em.inputs['Strength'])
    ntd.links.new(em.outputs[0], outn.inputs['Surface'])
    for o in scn.objects:
        if o.type == 'MESH':
            if not o.visible_camera:
                o.hide_render = True; continue
            o.data.materials.clear(); o.data.materials.append(dm)
            o.modifiers.clear() if o.name.startswith('cach') else None
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
    for o in scn.objects:
        if o.type == 'LIGHT': o.hide_render = True
    cam.data.dof.use_dof = False
    scn.cycles.samples = 4
    scn.cycles.use_denoising = False
    scn.view_settings.view_transform = 'Standard'; scn.view_settings.look = 'None'; scn.view_settings.exposure = 0
    scn.render.image_settings.file_format = 'OPEN_EXR'
    scn.render.image_settings.color_depth = '32'
else:
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_depth = '16'
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)

# print projection of key points for compositing
from bpy_extras.object_utils import world_to_camera_view
for nm, p in [('base', Vector((0, 0, 0))), ('top20', Vector((0, 0, 0.20))), ('plinth_r', Vector((0.118, 0, 0))), ('plinth_front', Vector((0, -0.118, 0))), ('plinth_back', Vector((0, 0.118, 0))), ('x17', Vector((0.085, 0, 0)))]:
    c = world_to_camera_view(scn, cam, p)
    print('PROJ', nm, round(c.x * RES_X, 2), round((1 - c.y) * RES_Y, 2))
