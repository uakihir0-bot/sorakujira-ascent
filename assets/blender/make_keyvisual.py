"""Key visual for SORAKUJIRA: the sky whale coiling through a golden cloud sea,
tiny Shizuku standing on a floating islet in the foreground, looking up.
Renders keyvisual.png (1280x720, Cycles) and saves keyvisual.blend.
"""
import bpy, math, os, random
from mathutils import Vector

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
random.seed(7)

def mat(name, color, roughness=0.5, emission=None, es=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = es
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "DITHERED"
    return m

def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

WHALE_MS = [mat(f"W{i}", lerp((0.05, 0.10, 0.26), (0.18, 0.30, 0.58), i / 4), 0.5) for i in range(5)]
BELLY_M = mat("Belly", (0.60, 0.70, 0.88), 0.6)
FIN_M = mat("Fin", (0.11, 0.22, 0.48), 0.5)
EYE_M = mat("Eye", (1.0, 0.8, 0.35), 0.25, emission=(1.0, 0.72, 0.25), es=4.0)
DOT_M = mat("Dot", (0.45, 0.95, 1.0), 0.4, emission=(0.4, 0.9, 1.0), es=2.4)
CLOUD_M = mat("Cloud", (1.0, 0.93, 0.86), 0.95)
CLOUD_M2 = mat("CloudShadow", (0.82, 0.78, 0.90), 0.95)
ROCK_M = mat("Rock", (0.35, 0.30, 0.38), 0.85)
MOSS_M = mat("MossTop", (0.55, 0.75, 0.55), 0.8)
CRY_M = mat("Crystal", (0.55, 0.42, 0.98), 0.2, emission=(0.5, 0.35, 1.0), es=0.8, alpha=0.92)
BODY_M = mat("ShizukuBody", (0.92, 0.96, 1.0), 0.22)
CORE_M = mat("Core", (0.35, 0.85, 1.0), 0.3, emission=(0.3, 0.8, 1.0), es=3.0)
PINK_M = mat("Pink", (1.0, 0.62, 0.70), 0.5)
BLACK_M = mat("Black", (0.02, 0.02, 0.04), 0.15)
HL_M = mat("HL", (1, 1, 1), 0.2, emission=(1, 1, 1), es=0.6)

def finish(o, material):
    if material: o.data.materials.append(material)
    if hasattr(o.data, "polygons"):
        for p in o.data.polygons: p.use_smooth = True
    return o

def sphere(name, loc, scale, material, seg=20, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    return finish(o, material)

# ================= WHALE (helix, centre pushed back) =================
CX, CY = -2.0, 16.0
def path(t):
    ang = t * math.radians(290)
    r = 11.0 * (1.0 - 0.42 * t)
    return (CX + r * math.cos(ang), CY + r * math.sin(ang), 3.0 + t * 50.0)

centers = []
N = 88
for i in range(N):
    t = i / (N - 1)
    x, y, z = path(t)
    br = 1.4 + 4.2 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t)) ** 0.7
    if t > 0.92: br *= 1.0 - (t - 0.92) * 1.2
    centers.append((x, y, z, br))
    sphere(f"Body{i}", (x, y, z), (br, br * 0.92, br * 1.02), WHALE_MS[min(4, int(t * 5))])
    sphere(f"Belly{i}", (x * 0.94 + CX * 0.06, y * 0.94 + CY * 0.06, z - br * 0.40),
           (br * 0.78, br * 0.72, br * 0.80), BELLY_M)

hx, hy, hz, hbr = centers[-1]
px, py, pz = path(0.965)
tan = Vector((hx - px, hy - py, hz - pz)); tan.normalize()
head_loc = Vector((hx, hy, hz)) + tan * 1.7 + Vector((0, 0, 0.5))
sphere("NeckBridge", tuple(Vector((hx, hy, hz)) + tan * 0.4), (4.2, 4.6, 3.9), WHALE_MS[4], seg=24, rings=18)
sphere("Head", tuple(head_loc), (4.6, 5.4, 4.3), WHALE_MS[4], seg=28, rings=20)
sphere("Jaw", tuple(head_loc + tan * 2.4 + Vector((0, 0, -2.4))), (3.6, 4.3, 2.0), BELLY_M, seg=24, rings=16)
sphere("EyeGreat", tuple(head_loc + Vector((4.4, -2.0, 1.3))), (1.05,) * 3, EYE_M)
sphere("EyeSmall", tuple(head_loc + Vector((-4.3, -1.6, 1.1))), (0.6,) * 3, EYE_M)
# tail fins
tx, ty, tz, _ = centers[0]
for s in (1, -1):
    f = sphere(f"Tail{s}", (tx + s * 4.2, ty + 1.0, tz - 1.6), (5.2, 0.95, 2.4), FIN_M)
    f.rotation_euler = (math.radians(8), math.radians(-16 * s), math.radians(24 * s))
# dorsal + pectoral fins
for idx, s in ((34, 1), (40, -1)):
    x, y, z, br = centers[idx]
    f = sphere(f"Pec{idx}", (x + s * (br + 2.4), y + 0.8, z - 1.0), (4.2, 0.7, 1.9), FIN_M)
    f.rotation_euler = (math.radians(-12), math.radians(10 * s), math.radians(28 * s))
for idx in (20, 50, 72):
    x, y, z, br = centers[idx]
    f = sphere(f"Dor{idx}", (x + (x - CX) * 0.28, y + (y - CY) * 0.28, z + br * 0.6), (0.65, 2.4, 3.2), FIN_M)
    f.rotation_euler = (0, math.atan2(y - CY, x - CX), math.radians(-14))
# plankton dots
for k in range(170):
    i = random.randrange(3, N - 1)
    x, y, z, br = centers[i]
    th = random.uniform(0, 2 * math.pi); ph = random.uniform(-0.5, 1.1)
    loc = (x + math.cos(th) * math.cos(ph) * br, y + math.sin(th) * math.cos(ph) * br * 0.94,
           z + math.sin(ph) * br * 1.03)
    r = random.uniform(0.09, 0.22)
    sphere(f"Dot{k}", loc, (r,) * 3, DOT_M, seg=8, rings=6)

# ================= CLOUD SEA =================
for k in range(110):
    x = random.uniform(-38, 38); y = random.uniform(-22, 34)
    z = random.uniform(-3.0, 3.5)
    s = random.uniform(2.4, 6.5)
    sphere(f"Cloud{k}", (x, y, z), (s, s * 0.78, s * 0.52), CLOUD_M if k % 3 else CLOUD_M2, seg=16, rings=12)

# ================= FOREGROUND ISLET + SHIZUKU =================
IX, IY, IZ = 14.0, -12.0, 9.0
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.4, radius2=3.6, depth=5.2, location=(IX, IY, IZ - 2.5))
finish(bpy.context.object, ROCK_M)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=3.6, depth=0.7, location=(IX, IY, IZ + 0.35))
finish(bpy.context.object, MOSS_M)
BASE = IZ + 0.7  # top of islet

# mini shizuku built at origin then moved as a group via parent empty
grp = bpy.data.objects.new("ShizukuKV", None); bpy.context.collection.objects.link(grp)
parts = []
profile = [(0.001, 0.00), (0.20, 0.02), (0.34, 0.10), (0.44, 0.26), (0.475, 0.44),
           (0.45, 0.60), (0.385, 0.76), (0.29, 0.90), (0.185, 1.02), (0.09, 1.12), (0.001, 1.20)]
verts, faces = [], []; SEG = 32
for r, z in profile:
    for i in range(SEG):
        a = 2 * math.pi * i / SEG; verts.append((r * math.cos(a), r * math.sin(a), z))
for j in range(len(profile) - 1):
    for i in range(SEG):
        a = j * SEG + i; b = j * SEG + (i + 1) % SEG; faces.append((a, b, b + SEG, a + SEG))
mesh = bpy.data.meshes.new("KVBody"); mesh.from_pydata(verts, [], faces); mesh.update()
o = bpy.data.objects.new("KVBody", mesh); bpy.context.collection.objects.link(o); finish(o, BODY_M); parts.append(o)
def part(name, loc, scale, material):
    p = sphere(name, loc, scale, material); parts.append(p); return p
part("KVCore", (0, -0.425, 0.44), (0.165, 0.11, 0.20), CORE_M)
f = part("KVFinL", (-0.22, 0.07, 1.18), (0.085, 0.045, 0.34), PINK_M); f.rotation_euler = (math.radians(-20), math.radians(-28), 0)
f = part("KVFinR", (0.22, 0.07, 1.18), (0.085, 0.045, 0.34), PINK_M); f.rotation_euler = (math.radians(-20), math.radians(28), 0)
part("KVEyeL", (-0.175, -0.415, 0.74), (0.052, 0.03, 0.078), BLACK_M)
part("KVEyeR", (0.175, -0.415, 0.74), (0.052, 0.03, 0.078), BLACK_M)
part("KVHL_L", (-0.192, -0.442, 0.775), (0.016, 0.01, 0.024), HL_M)
part("KVHL_R", (0.158, -0.442, 0.775), (0.016, 0.01, 0.024), HL_M)
part("KVCheekL", (-0.295, -0.375, 0.60), (0.075, 0.04, 0.055), PINK_M)
part("KVCheekR", (0.295, -0.375, 0.60), (0.075, 0.04, 0.055), PINK_M)
for p in parts: p.parent = grp
grp.location = (IX - 0.6, IY - 0.4, BASE)
grp.scale = (3.0, 3.0, 3.0)
grp.rotation_euler = (0, 0, math.radians(155))  # face three-quarter toward whale & camera

# floating crystals around
def crystal(loc, h, r, tilt):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, radius2=0.0, depth=h, location=loc)
    o = bpy.context.object; finish(o, CRY_M); o.rotation_euler = tilt
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.0, radius2=r * 0.9, depth=h * 0.42,
                                    location=(loc[0], loc[1], loc[2] - h * 0.68))
    o2 = bpy.context.object; finish(o2, CRY_M); o2.rotation_euler = tilt
crystal((3.0, 0.0, 14.0), 4.2, 0.85, (math.radians(12), 0, math.radians(-8)))
crystal((19.0, 4.0, 20.0), 5.0, 1.0, (math.radians(-8), 0, math.radians(10)))
crystal((-14.0, 8.0, 30.0), 4.4, 0.9, (math.radians(6), 0, math.radians(14)))
crystal((IX + 4.2, IY + 1.5, BASE + 2.6), 2.2, 0.5, (math.radians(-10), 0, math.radians(-12)))
# glowing particles
for k in range(130):
    loc = (random.uniform(-20, 22), random.uniform(-6, 30), random.uniform(2, 52))
    r = random.uniform(0.06, 0.16)
    sphere(f"Spark{k}", loc, (r,) * 3, DOT_M, seg=6, rings=5)

# ================= WORLD / LIGHTS / CAMERA =================
world = bpy.data.worlds.new("SkyWorld"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.10, 0.12, 0.30, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.35
# gradient sky dome: emissive sphere with a Z-driven colour ramp (peach horizon -> indigo zenith)
dome_m = bpy.data.materials.new("SkyDome"); dome_m.use_nodes = True
dn = dome_m.node_tree; dn.nodes.clear()
dout = dn.nodes.new("ShaderNodeOutputMaterial")
demit = dn.nodes.new("ShaderNodeEmission"); demit.inputs["Strength"].default_value = 0.9
dtex = dn.nodes.new("ShaderNodeTexCoord")
dsep = dn.nodes.new("ShaderNodeSeparateXYZ")
dramp = dn.nodes.new("ShaderNodeValToRGB")
dramp.color_ramp.elements[0].position = 0.40; dramp.color_ramp.elements[0].color = (1.0, 0.52, 0.28, 1)
_e = dramp.color_ramp.elements.new(0.50); _e.color = (0.92, 0.45, 0.52, 1)
_e = dramp.color_ramp.elements.new(0.57); _e.color = (0.36, 0.30, 0.66, 1)
dramp.color_ramp.elements[1].position = 0.64; dramp.color_ramp.elements[1].color = (0.07, 0.09, 0.30, 1)
dn.links.new(dtex.outputs["Generated"], dsep.inputs["Vector"])
dn.links.new(dsep.outputs["Z"], dramp.inputs["Fac"])
dn.links.new(dramp.outputs["Color"], demit.inputs["Color"])
dn.links.new(demit.outputs[0], dout.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=24, radius=260, location=(0, 10, 20))
dome = bpy.context.object; dome.name = "SkyDome"; dome.data.materials.append(dome_m)

def sun(name, loc, energy, color, size=6):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = "DISK"; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 8, 20)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
sun("SunWarm", (-30, -6, 55), 3000, (1.0, 0.72, 0.45))
sun("FillCool", (26, -24, 20), 900, (0.55, 0.70, 1.0))
d = bpy.data.lights.new("EyeGlow", "POINT"); d.energy = 2600; d.color = (1.0, 0.75, 0.35)
o = bpy.data.objects.new("EyeGlow", d); scene.collection.objects.link(o); o.location = tuple(head_loc + Vector((5.5, -5.0, 1.5)))

cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 24
cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (34, -52, 20)
cam.rotation_euler = (Vector((-2, 10, 27)) - cam.location).to_track_quat("-Z", "Y").to_euler()

scene.render.engine = "CYCLES"
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.cycles.device = "CPU"
scene.render.resolution_x = 1280; scene.render.resolution_y = 720
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(OUT, "keyvisual.png")
scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = 0.35

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "keyvisual.blend"))
bpy.ops.render.render(write_still=True)
print("KEYVISUAL DONE")
