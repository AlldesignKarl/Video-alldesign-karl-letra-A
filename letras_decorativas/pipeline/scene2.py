"""Studio set for the decorative-letter spot: warm blush plaster wall with window light and leaf
shadows, cream travertine tabletop, out-of-focus props (ceramic vase with dried pampas, dusty-rose
books, candle). The product itself is composited later from the photographs."""
import bpy, math, sys, random
from mathutils import Vector, Euler, Matrix

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RES_X, RES_Y, SAMPLES = int(args[0]), int(args[1]), int(args[2])
OUT, ELEV_DEG, MODE = args[3], float(args[4]), args[5]   # MODE: beauty | depth
WIDE = RES_X / RES_Y / (1080 / 1920)                    # extra horizontal room for camera pans
random.seed(5)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.render.resolution_x, scn.render.resolution_y = RES_X, RES_Y
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'
scn.view_settings.exposure = -0.15
scn.cycles.max_bounces = 8
scn.cycles.blur_glossy = 0.5


def srgb(r, g, b):
    def c(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c(r), c(g), c(b), 1.0)


def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']


def noise_ramp(nt, b, c0, c1, scale, detail=8, coord='Object', rough=0.6, mapping_scale=None):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale
    n1.inputs['Detail'].default_value = detail; n1.inputs['Roughness'].default_value = rough
    src = tc.outputs[coord]
    if mapping_scale:
        mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = mapping_scale
        nt.links.new(src, mp.inputs['Vector']); src = mp.outputs['Vector']
    nt.links.new(src, n1.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = c0; ramp.color_ramp.elements[1].color = c1
    nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    return tc, src


# ---------------------------------------------------------------- materials
wall_m, nt, b = new_mat('wall')
tc, src = noise_ramp(nt, b, srgb(228, 204, 196), srgb(244, 230, 222), 5, 8, rough=0.62)
n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 70; n2.inputs['Detail'].default_value = 4
nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.22; bump.inputs['Distance'].default_value = 0.003
nt.links.new(n2.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
b.inputs['Roughness'].default_value = 0.93

# cream travertine tabletop (satin, horizontal veining)
trav_m, nt, b = new_mat('travertine')
tc = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.5, 4, 1)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 2.2; n1.inputs['Detail'].default_value = 10; n1.inputs['Distortion'].default_value = 0.5
nt.links.new(mp.outputs['Vector'], n1.inputs['Vector'])
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = srgb(226, 210, 196)
ramp.color_ramp.elements[1].color = srgb(242, 232, 220)
nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 220
nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
pits = nt.nodes.new('ShaderNodeMath'); pits.operation = 'LESS_THAN'; pits.inputs[1].default_value = 0.05
nt.links.new(vor.outputs['Distance'], pits.inputs[0])
dark = nt.nodes.new('ShaderNodeMix'); dark.data_type = 'RGBA'; dark.blend_type = 'MULTIPLY'
nt.links.new(pits.outputs[0], dark.inputs['Factor'])
nt.links.new(ramp.outputs['Color'], dark.inputs[6]); dark.inputs[7].default_value = srgb(205, 190, 175)
nt.links.new(dark.outputs[2], b.inputs['Base Color'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.001
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
nt.links.new(pits.outputs[0], inv.inputs[1]); nt.links.new(inv.outputs[0], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
b.inputs['Roughness'].default_value = 0.5

cer_m, nt, b = new_mat('ceramic')            # matte cream stoneware
noise_ramp(nt, b, srgb(226, 214, 200), srgb(240, 232, 222), 18, 6)
b.inputs['Roughness'].default_value = 0.75

pampas_m, nt, b = new_mat('pampas')
b.inputs['Base Color'].default_value = srgb(226, 200, 176)
b.inputs['Roughness'].default_value = 0.9
b.inputs['Subsurface Weight'].default_value = 0.3
b.inputs['Sheen Weight'].default_value = 0.8
stem_m, nt, b = new_mat('stem'); b.inputs['Base Color'].default_value = srgb(196, 168, 130)

rose_m, nt, b = new_mat('book_rose'); b.inputs['Base Color'].default_value = srgb(196, 132, 132); b.inputs['Roughness'].default_value = 0.8
b.inputs['Sheen Weight'].default_value = 0.4
blush_m, nt, b = new_mat('book_blush'); b.inputs['Base Color'].default_value = srgb(232, 196, 190); b.inputs['Roughness'].default_value = 0.85
pages_m, nt, b = new_mat('pages'); b.inputs['Base Color'].default_value = srgb(242, 234, 222); b.inputs['Roughness'].default_value = 0.9
wax_m, nt, b = new_mat('wax'); b.inputs['Base Color'].default_value = srgb(244, 236, 226)
b.inputs['Subsurface Weight'].default_value = 0.6; b.inputs['Subsurface Radius'].default_value = (0.02, 0.012, 0.008); b.inputs['Roughness'].default_value = 0.45
glass_m, nt, b = new_mat('glass'); b.inputs['Base Color'].default_value = srgb(246, 222, 216)
b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.08; b.inputs['IOR'].default_value = 1.45
leaf_m, nt, b = new_mat('leaf')

# ---------------------------------------------------------------- geometry
WALL_Y = 0.95
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, WALL_Y, 1.5), rotation=(math.radians(90), 0, 0))
bpy.context.active_object.data.materials.append(wall_m)
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, WALL_Y - 4, 0))
bpy.context.active_object.data.materials.append(trav_m)

# vase with dried pampas, back right
VX, VY = 0.20, 0.40
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.075, location=(VX, VY, 0.085))
o = bpy.context.active_object; o.scale = (1, 1, 1.15); o.data.materials.append(cer_m); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.03, depth=0.16, location=(VX, VY, 0.22))
o = bpy.context.active_object; o.data.materials.append(cer_m); bpy.ops.object.shade_smooth()
for i in range(9):
    ang = random.uniform(-0.55, 0.35); ang2 = random.uniform(-0.35, 0.35)
    L = random.uniform(0.15, 0.25)
    base = Vector((VX, VY, 0.29))
    d = Vector((math.sin(ang), math.sin(ang2) * 0.6, math.cos(ang))).normalized()
    mid = base + d * L / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0022, depth=L, location=mid)
    st = bpy.context.active_object; st.rotation_mode = 'QUATERNION'
    st.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d); st.data.materials.append(stem_m)
    for k in range(14):                       # fluffy plume made of soft ellipsoids
        p = base + d * (L + 0.012 * k - 0.05) + Vector((random.uniform(-.012, .012), random.uniform(-.012, .012), 0))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.022 - 0.0009 * k, location=p)
        pl = bpy.context.active_object; pl.rotation_mode = 'QUATERNION'
        pl.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d); pl.scale = (0.8, 0.8, 1.9)
        pl.data.materials.append(pampas_m); bpy.ops.object.shade_smooth()

# stacked books + candle in glass, back left
def box(size, loc, rotz, mat, bevel=0.003):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, math.radians(rotz)))
    o = bpy.context.active_object; o.scale = size; bpy.ops.object.transform_apply(scale=True)
    m = o.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = 3
    o.data.materials.append(mat); return o
box((0.24, 0.17, 0.03), (-0.215, 0.38, 0.015), -8, rose_m)
box((0.232, 0.162, 0.024), (-0.211, 0.38, 0.015), -8, pages_m, 0.001)
box((0.21, 0.15, 0.026), (-0.205, 0.37, 0.043), -2, blush_m)
box((0.202, 0.142, 0.020), (-0.201, 0.37, 0.043), -2, pages_m, 0.001)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.042, depth=0.085, location=(-0.19, 0.37, 0.056 + 0.0425))
o = bpy.context.active_object; o.data.materials.append(glass_m); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.036, depth=0.06, location=(-0.19, 0.37, 0.058 + 0.03))
o = bpy.context.active_object; o.data.materials.append(wax_m); bpy.ops.object.shade_smooth()

# ---------------------------------------------------------------- lights
world = bpy.data.worlds.new('w'); scn.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = srgb(238, 222, 210); bg.inputs['Strength'].default_value = 0.25

sun_dir = Vector((0.80, 0.50, -0.33)).normalized()
bpy.ops.object.light_add(type='SUN', location=(0, 0, 2))
sun = bpy.context.active_object
sun.data.energy = 3.4; sun.data.angle = math.radians(2.2); sun.data.color = (1.0, 0.80, 0.60)
sun.rotation_mode = 'QUATERNION'; sun.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(sun_dir)

wc = Vector((0.02, WALL_Y, 0.30)) - sun_dir * 1.5
u = sun_dir.cross(Vector((0, 0, 1))).normalized(); v = u.cross(sun_dir).normalized()
M = Matrix((u, v, -sun_dir)).transposed()


def occluder(cu, cv, su, sv):
    bpy.ops.mesh.primitive_plane_add(size=1, location=wc + u * cu + v * cv)
    o = bpy.context.active_object; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = M.to_quaternion()
    o.scale = (su, sv, 1); o.data.materials.append(leaf_m)
    o.visible_camera = False; o.visible_glossy = False; o.visible_diffuse = False
W, H = 0.5, 0.75
occluder(0, H / 2 + 1.5, 6, 3); occluder(0, -H / 2 - 1.5, 6, 3)
occluder(-W / 2 - 1.5, 0, 3, 6); occluder(W / 2 + 1.5, 0, 3, 6)
occluder(0, 0.12, W, 0.03); occluder(0.02, 0, 0.03, H)
# a leafy branch between window and wall -> soft dappled shadow
olive_c = wc + sun_dir * 0.6 + u * 0.12 + v * 0.25
for br in range(3):
    p = olive_c + u * random.uniform(-0.18, 0.18) + v * random.uniform(-0.12, 0.12)
    dirv = (u * random.uniform(-1, 1) + v * random.uniform(-0.6, 0.2)).normalized()
    for i in range(20):
        p = p + dirv * 0.02
        dirv = (dirv + (u * random.uniform(-0.25, 0.25) + v * random.uniform(-0.25, 0.25))).normalized()
        side = 1 if i % 2 == 0 else -1
        leafdir = (dirv + (u if side > 0 else -u) * 0.8).normalized()
        bpy.ops.mesh.primitive_plane_add(size=1, location=p + leafdir * 0.03)
        lf = bpy.context.active_object
        a = math.atan2(leafdir.dot(v), leafdir.dot(u))
        lf.rotation_mode = 'QUATERNION'
        lf.rotation_quaternion = M.to_quaternion() @ Euler((random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4), a)).to_quaternion()
        lf.scale = (0.066, 0.014, 1); lf.data.materials.append(leaf_m)
        lf.visible_camera = False; lf.visible_glossy = False; lf.visible_diffuse = False

bpy.ops.object.light_add(type='AREA', location=(-1.0, -0.9, 0.9))
key = bpy.context.active_object
key.data.shape = 'RECTANGLE'; key.data.size = 1.4; key.data.size_y = 1.8; key.data.energy = 75; key.data.color = (1.0, 0.91, 0.82)
key.rotation_mode = 'QUATERNION'; key.rotation_quaternion = Vector((0, 0, -1)).rotation_difference((Vector((0, 0.1, 0.1)) - key.location).normalized())
bpy.ops.object.light_add(type='AREA', location=(1.0, -0.7, 0.45))
fill = bpy.context.active_object
fill.data.size = 1.2; fill.data.energy = 16; fill.data.color = (1.0, 0.93, 0.90)
fill.rotation_mode = 'QUATERNION'; fill.rotation_quaternion = Vector((0, 0, -1)).rotation_difference((Vector((0, 0, 0.1)) - fill.location).normalized())

# ---------------------------------------------------------------- camera
DIST = 1.25
ELEV = math.radians(ELEV_DEG)
AIM = Vector((0, 0, 0.165))
cam_loc = Vector((0, 0, 0.10)) + Vector((0, -math.cos(ELEV), math.sin(ELEV))) * DIST
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.active_object
cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (AIM - cam_loc).to_track_quat('-Z', 'Y')
cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 36; cam.data.lens = 88
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (Vector((0, 0, 0.1)) - cam_loc).length
cam.data.dof.aperture_fstop = 2.2; cam.data.dof.aperture_blades = 9
scn.camera = cam

if MODE == 'depth':
    dm = bpy.data.materials.new('depthmat'); dm.use_nodes = True
    ntd = dm.node_tree
    for nd in list(ntd.nodes): ntd.nodes.remove(nd)
    camd = ntd.nodes.new('ShaderNodeCameraData'); mul = ntd.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.1
    em = ntd.nodes.new('ShaderNodeEmission'); outn = ntd.nodes.new('ShaderNodeOutputMaterial')
    ntd.links.new(camd.outputs['View Z Depth'], mul.inputs[0]); ntd.links.new(mul.outputs[0], em.inputs['Strength'])
    ntd.links.new(em.outputs[0], outn.inputs['Surface'])
    for o in scn.objects:
        if o.type == 'MESH':
            if not o.visible_camera: o.hide_render = True; continue
            o.data.materials.clear(); o.data.materials.append(dm); o.modifiers.clear()
        if o.type == 'LIGHT': o.hide_render = True
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
    cam.data.dof.use_dof = False; scn.cycles.samples = 4; scn.cycles.use_denoising = False
    scn.view_settings.view_transform = 'Standard'; scn.view_settings.look = 'None'; scn.view_settings.exposure = 0
    scn.render.image_settings.file_format = 'OPEN_EXR'; scn.render.image_settings.color_depth = '32'
else:
    scn.render.image_settings.file_format = 'PNG'; scn.render.image_settings.color_depth = '16'
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)

from bpy_extras.object_utils import world_to_camera_view
for nm, p in [('base', Vector((0, 0, 0))), ('top20', Vector((0, 0, 0.20))), ('x10', Vector((0.10, 0, 0)))]:
    c = world_to_camera_view(scn, cam, p)
    print('PROJ', nm, round(c.x * RES_X, 2), round((1 - c.y) * RES_Y, 2))
