"""Key visual for SORAKUJIRA — round 3 (AAA-aspiring rework).

Golden-hour key art: the colossal sky whale coiling diagonally through the
frame (tail lost in the cloud sea, full head inside the top third, a gentle
iris-and-pupil eye looking down), tiny-but-readable Shizuku on a foreground
islet gazing up, warm back/rim sun + cool fill, sun glow disc, compositor
Fog Glow, gentle camera DOF focused on Shizuku.

Env KV_MODE=preview renders a fast 640x360 check to /tmp/kv_preview.png.
Final: 1280x720, 96 samples -> assets/keyvisual.png + keyvisual.blend.
"""
import bpy, math, os, random
from mathutils import Vector

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.environ.get("KV_MODE") == "preview"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
random.seed(11)

CAM_POS = Vector((27.0, -52.0, 13.0))
CAM_TGT = Vector((-3.0, 10.0, 23.0))
CHAR_POS = Vector((14.4, -15.6, 8.2))          # feet of Shizuku (islet top)
SUN_POS = Vector((-52.0, 30.0, 27.0))          # sun glow disc, low on the horizon behind the whale, frame-left

# ---------------------------------------------------------------- materials
def mat(name, color, roughness=0.5, emission=None, es=0.0, alpha=1.0, clearcoat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    if clearcoat:
        try: b.inputs["Coat Weight"].default_value = clearcoat
        except Exception: pass
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = es
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "DITHERED"
    return m

def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

WHALE_MS = [mat(f"W{i}", lerp((0.045, 0.075, 0.235), (0.17, 0.29, 0.56), i / 4), 0.38, clearcoat=0.5) for i in range(5)]
BELLY_M = mat("Belly", (0.62, 0.72, 0.88), 0.55)
FIN_M = mat("Fin", (0.10, 0.20, 0.46), 0.42, clearcoat=0.4)
IRIS_M = mat("Iris", (0.85, 0.55, 0.16), 0.18, emission=(0.95, 0.55, 0.15), es=0.55, clearcoat=0.8)
PUPIL_M = mat("Pupil", (0.015, 0.012, 0.02), 0.08, clearcoat=0.9)
DOT_M = mat("Dot", (0.45, 0.95, 1.0), 0.4, emission=(0.4, 0.9, 1.0), es=2.2)
DOTG_M = mat("DotGold", (1.0, 0.8, 0.4), 0.4, emission=(1.0, 0.72, 0.3), es=2.0)
CLOUD_M = mat("Cloud", (1.02, 0.95, 0.88), 0.95)
CLOUD_M2 = mat("CloudShadow", (0.78, 0.74, 0.90), 0.95)
ROCK_M = mat("Rock", (0.32, 0.27, 0.36), 0.85)
MOSS_M = mat("MossTop", (0.48, 0.70, 0.50), 0.8)
CRY_M = mat("Crystal", (0.58, 0.45, 0.99), 0.18, emission=(0.52, 0.36, 1.0), es=1.1, alpha=0.94)
CRYC_M = mat("CrystalCyan", (0.40, 0.85, 1.0), 0.18, emission=(0.3, 0.75, 1.0), es=1.1, alpha=0.94)
BODY_M = mat("ShizukuBody", (0.93, 0.96, 1.0), 0.2, clearcoat=0.6)
CORE_M = mat("Core", (0.35, 0.85, 1.0), 0.25, emission=(0.3, 0.8, 1.0), es=2.6)
PINK_M = mat("Pink", (1.0, 0.62, 0.70), 0.45)
BLACK_M = mat("Black", (0.02, 0.02, 0.04), 0.12, clearcoat=0.8)
HL_M = mat("HL", (1, 1, 1), 0.2, emission=(1, 1, 1), es=0.8)
BIRD_M = mat("Bird", (0.05, 0.05, 0.10), 0.9)

def finish(o, material):
    if material: o.data.materials.append(material)
    if hasattr(o.data, "polygons"):
        for p in o.data.polygons: p.use_smooth = True
    o.cycles.use_adaptive_subdivision = False
    return o

def sphere(name, loc, scale, material, seg=20, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    return finish(o, material)

# ================================================================ THE WHALE
CX, CY = -4.0, 14.0
def path(t):
    ang = t * math.radians(300)
    r = 10.5 * (1.0 - 0.45 * t)
    return (CX + r * math.cos(ang), CY + r * math.sin(ang), 2.0 + t * 44.0)

centers = []
N = 115
for i in range(N):
    t = i / (N - 1)
    x, y, z = path(t)
    # fat majestic body: thin tail -> broad mid -> gentle taper to neck
    br = 0.9 + 5.3 * math.sin(math.pi * (0.12 + 0.76 * t)) ** 0.8
    if t > 0.90: br *= 1.0 - (t - 0.90) * 2.2
    centers.append((x, y, z, br))
    sphere(f"Body{i}", (x, y, z), (br, br * 0.94, br * 1.04), WHALE_MS[min(4, int(t * 5))], seg=24, rings=18)
    sphere(f"Belly{i}", (x, y - br * 0.30, z - br * 0.42), (br * 0.76, br * 0.70, br * 0.82), BELLY_M, seg=18, rings=12)

hx, hy, hz, hbr = centers[-1]
px, py, pz = path(0.962)
tan = Vector((hx - px, hy - py, hz - pz)); tan.normalize()
head_loc = Vector((hx, hy, hz)) + tan * 2.0 + Vector((0, 0, 0.6))
sphere("NeckBridge", tuple(Vector((hx, hy, hz)) + tan * 0.5), (4.9, 5.2, 4.6), WHALE_MS[4], seg=24, rings=18)
sphere("Head", tuple(head_loc), (5.1, 5.9, 4.6), WHALE_MS[4], seg=32, rings=24)
sphere("Melon", tuple(head_loc + tan * 1.6 + Vector((0, 0, 2.2))), (3.9, 4.4, 3.2), WHALE_MS[4], seg=24, rings=18)
sphere("Jaw", tuple(head_loc + tan * 3.1 + Vector((0, 0, -2.6))), (3.9, 4.6, 2.1), BELLY_M, seg=24, rings=16)

# --- the eye: golden iris + dark pupil glancing down at Shizuku, gentle glow.
# Place it ON the ellipsoid surface (offset = effective radius along dir_cam)
# so it can never sink inside the head.
dir_cam = (CAM_POS - head_loc); dir_cam.normalize()
dir_chr = (CHAR_POS - head_loc); dir_chr.normalize()
HS = (5.1, 5.9, 4.6)  # Head sphere scale
r_eff = 1.0 / math.sqrt((dir_cam.x / HS[0]) ** 2 + (dir_cam.y / HS[1]) ** 2 + (dir_cam.z / HS[2]) ** 2)
eye_c = head_loc + dir_cam * (r_eff * 0.96) + Vector((0, 0, 0.35))
sphere("Iris", tuple(eye_c), (1.18,) * 3, IRIS_M, seg=28, rings=20)
pup_c = eye_c + dir_cam * 0.80 + dir_chr * 0.34
sphere("Pupil", tuple(pup_c), (0.60,) * 3, PUPIL_M, seg=22, rings=16)
sphere("EyeHL", tuple(pup_c + dir_cam * 0.44 + Vector((0.12, 0.06, 0.34))), (0.17,) * 3, HL_M, seg=10, rings=8)
# small far eye on the head's other side (surface-placed the same way)
dir_far = -dir_cam
r_far = 1.0 / math.sqrt((dir_far.x / HS[0]) ** 2 + (dir_far.y / HS[1]) ** 2 + (dir_far.z / HS[2]) ** 2)
eye2_c = head_loc + dir_far * (r_far * 0.96) + Vector((0, 0, 0.3))
sphere("IrisFar", tuple(eye2_c), (0.72,) * 3, IRIS_M, seg=18, rings=12)

# tail flukes (broad, horizontal) at the bottom, dipping into the clouds
tx, ty, tz, _ = centers[0]
for s in (1, -1):
    f = sphere(f"Fluke{s}", (tx + s * 4.6, ty + 0.6, tz + 0.4), (5.6, 1.05, 2.5), FIN_M, seg=20, rings=12)
    f.rotation_euler = (math.radians(6), math.radians(-14 * s), math.radians(20 * s))
# pectoral fins
for idx, s in ((36, 1), (44, -1)):
    x, y, z, br = centers[idx]
    f = sphere(f"Pec{idx}", (x + s * (br + 3.0), y + 0.6, z - 1.4), (6.2, 0.85, 2.7), FIN_M, seg=18, rings=12)
    f.rotation_euler = (math.radians(-10), math.radians(12 * s), math.radians(30 * s))
# dorsal sail fins along the outer back
for idx in (18, 48, 74):
    x, y, z, br = centers[idx]
    ox, oy = (x - CX), (y - CY); ol = math.hypot(ox, oy) or 1.0
    f = sphere(f"Dor{idx}", (x + ox / ol * br * 0.75, y + oy / ol * br * 0.75, z + br * 0.45),
               (0.7, 2.6, 3.4), FIN_M, seg=16, rings=10)
    f.rotation_euler = (0, math.atan2(oy, ox), math.radians(-16))
# plankton sparkle concentrated on the camera-facing flank
for k in range(260):
    i = random.randrange(3, N - 1)
    x, y, z, br = centers[i]
    base_ang = math.atan2(CAM_POS.y - y, CAM_POS.x - x)
    th = base_ang + random.gauss(0, 0.85)
    ph = random.uniform(-0.45, 1.05)
    loc = (x + math.cos(th) * math.cos(ph) * br * 1.01, y + math.sin(th) * math.cos(ph) * br * 0.95,
           z + math.sin(ph) * br * 1.05)
    r = random.uniform(0.08, 0.20)
    sphere(f"Dot{k}", loc, (r,) * 3, DOT_M if k % 4 else DOTG_M, seg=8, rings=6)
# a small crown of crystals riding near the head
for k in range(5):
    a = k * 2.4
    loc = head_loc + Vector((math.cos(a) * 4.4, math.sin(a) * 4.4, 3.6 + 0.7 * math.sin(a * 2)))
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.42, radius2=0.0, depth=1.9, location=tuple(loc))
    o = bpy.context.object; finish(o, CRYC_M); o.rotation_euler = (math.radians(14), 0, math.radians(a * 20))

# ================================================================ CLOUD SEA
for k in range(150):
    x = random.uniform(-42, 42); y = random.uniform(-26, 38)
    z = random.uniform(-4.0, 3.2) - 0.012 * (x * x) * 0.02
    s = random.uniform(2.2, 8.5)
    sphere(f"Cloud{k}", (x, y, z), (s, s * 0.80, s * 0.50),
           CLOUD_M if k % 3 else CLOUD_M2, seg=16, rings=12)
# a few far cloud clusters low on the horizon (never high: backlit puffs read as discs)
for k in range(10):
    x = random.uniform(-44, 34); y = random.uniform(26, 46)
    z = random.uniform(-2, 6); s = random.uniform(4.0, 8.0)
    sphere(f"HiCloud{k}", (x, y, z), (s, s * 0.72, s * 0.45), CLOUD_M, seg=12, rings=9)

# ================================================================ ISLETS
def islet(x, y, top_z, rad, with_crystal=True):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.35, radius2=rad, depth=rad * 1.55,
                                    location=(x, y, top_z - rad * 0.78 - 0.3))
    finish(bpy.context.object, ROCK_M)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=rad, depth=0.6, location=(x, y, top_z - 0.3))
    finish(bpy.context.object, MOSS_M)
    if with_crystal:
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=rad * 0.16, radius2=0.0, depth=rad * 0.75,
                                        location=(x + rad * 0.55, y + rad * 0.3, top_z + rad * 0.32))
        o = bpy.context.object; finish(o, CRY_M); o.rotation_euler = (math.radians(8), 0, math.radians(-10))

islet(CHAR_POS.x, CHAR_POS.y, CHAR_POS.z, 4.3)                    # hero islet
islet(4.0, -5.0, 13.5, 2.5)                                       # chain toward the whale
islet(-3.5, 3.0, 20.0, 2.0)
islet(-7.0, 7.5, 27.0, 1.6, with_crystal=False)
islet(11.0, 10.0, 17.0, 1.3)

# ================================================================ SHIZUKU (hero, ~1.6x)
grp = bpy.data.objects.new("ShizukuKV", None); bpy.context.collection.objects.link(grp)
parts = []
profile = [(0.001, 0.00), (0.20, 0.02), (0.34, 0.10), (0.44, 0.26), (0.475, 0.44),
           (0.45, 0.60), (0.385, 0.76), (0.29, 0.90), (0.185, 1.02), (0.09, 1.12), (0.001, 1.20)]
verts, faces = [], []; SEG = 40
for r, z in profile:
    for i in range(SEG):
        a = 2 * math.pi * i / SEG; verts.append((r * math.cos(a), r * math.sin(a), z))
for j in range(len(profile) - 1):
    for i in range(SEG):
        a = j * SEG + i; b = j * SEG + (i + 1) % SEG; faces.append((a, b, b + SEG, a + SEG))
mesh = bpy.data.meshes.new("KVBody"); mesh.from_pydata(verts, [], faces); mesh.update()
o = bpy.data.objects.new("KVBody", mesh); bpy.context.collection.objects.link(o); finish(o, BODY_M); parts.append(o)
def part(name, loc, scale, material, seg=18, rings=12):
    p = sphere(name, loc, scale, material, seg=seg, rings=rings); parts.append(p); return p
part("KVCore", (0, -0.40, 0.42), (0.185, 0.13, 0.225), CORE_M, seg=20, rings=14)
# long ribbon fins sweeping back/up from the head (rim light catches these)
f = part("KVFinL", (-0.235, 0.10, 1.22), (0.095, 0.05, 0.42), PINK_M); f.rotation_euler = (math.radians(-26), math.radians(-30), 0)
f = part("KVFinR", (0.235, 0.10, 1.22), (0.095, 0.05, 0.42), PINK_M); f.rotation_euler = (math.radians(-26), math.radians(30), 0)
f = part("KVFinL2", (-0.15, 0.16, 1.13), (0.06, 0.035, 0.26), PINK_M); f.rotation_euler = (math.radians(-38), math.radians(-42), 0)
f = part("KVFinR2", (0.15, 0.16, 1.13), (0.06, 0.035, 0.26), PINK_M); f.rotation_euler = (math.radians(-38), math.radians(42), 0)
# tail ribbon behind
f = part("KVTail", (0, 0.34, 0.30), (0.10, 0.30, 0.07), PINK_M); f.rotation_euler = (math.radians(38), 0, 0)
part("KVEyeL", (-0.175, -0.415, 0.74), (0.055, 0.032, 0.082), BLACK_M, seg=16, rings=12)
part("KVEyeR", (0.175, -0.415, 0.74), (0.055, 0.032, 0.082), BLACK_M, seg=16, rings=12)
part("KVHL_L", (-0.193, -0.444, 0.778), (0.017, 0.01, 0.026), HL_M, seg=8, rings=6)
part("KVHL_R", (0.157, -0.444, 0.778), (0.017, 0.01, 0.026), HL_M, seg=8, rings=6)
part("KVCheekL", (-0.30, -0.375, 0.60), (0.08, 0.042, 0.058), PINK_M)
part("KVCheekR", (0.30, -0.375, 0.60), (0.08, 0.042, 0.058), PINK_M)
# tiny feet
part("KVFootL", (-0.20, -0.16, 0.045), (0.13, 0.20, 0.06), BODY_M)
part("KVFootR", (0.20, -0.16, 0.045), (0.13, 0.20, 0.06), BODY_M)
for p in parts: p.parent = grp
grp.location = tuple(CHAR_POS)
grp.scale = (4.8, 4.8, 4.8)
# face the camera three-quarter (default face = -Y), chin tipped up toward the whale
grp.rotation_euler = (math.radians(-11), 0, math.radians(16))

# ================================================================ CRYSTALS / SPARKS / BIRDS
def crystal(loc, h, r, tilt, m=CRY_M):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, radius2=0.0, depth=h, location=loc)
    o = bpy.context.object; finish(o, m); o.rotation_euler = tilt
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.0, radius2=r * 0.9, depth=h * 0.42,
                                    location=(loc[0], loc[1], loc[2] - h * 0.68))
    o2 = bpy.context.object; finish(o2, m); o2.rotation_euler = tilt
crystal((1.0, 2.0, 16.5), 4.6, 0.9, (math.radians(12), 0, math.radians(-8)))
crystal((17.5, 3.0, 23.0), 5.4, 1.05, (math.radians(-8), 0, math.radians(10)), CRYC_M)
crystal((-15.5, 9.0, 33.0), 4.8, 0.95, (math.radians(6), 0, math.radians(14)))
crystal((CHAR_POS.x + 4.6, CHAR_POS.y + 1.6, CHAR_POS.z + 2.4), 2.4, 0.55, (math.radians(-10), 0, math.radians(-12)), CRYC_M)
crystal((-11.0, -2.0, 10.5), 3.2, 0.7, (math.radians(-14), 0, math.radians(6)))
for k in range(150):
    loc = (random.uniform(-22, 24), random.uniform(-8, 32), random.uniform(2, 54))
    r = random.uniform(0.06, 0.17)
    sphere(f"Spark{k}", loc, (r,) * 3, DOT_M if k % 3 else DOTG_M, seg=6, rings=5)
# distant bird / sky-fish silhouettes for scale
for k in range(8):
    bx, by, bz = random.uniform(-30, 18), random.uniform(26, 46), random.uniform(18, 44)
    s = random.uniform(0.8, 1.5)
    for w in (1, -1):
        bpy.ops.mesh.primitive_cube_add(location=(bx + w * 0.55 * s, by, bz + 0.12 * s))
        o = bpy.context.object; o.scale = (0.62 * s, 0.10 * s, 0.055 * s)
        o.rotation_euler = (0, math.radians(18 * w), math.radians(10 * w)); finish(o, BIRD_M)
    bpy.ops.mesh.primitive_cube_add(location=(bx, by, bz))
    o = bpy.context.object; o.scale = (0.30 * s, 0.13 * s, 0.07 * s); finish(o, BIRD_M)

# ================================================================ SKY (world gradient) + SUN GLOW
# World background driven by the camera-ray direction (Geometry > Incoming):
# robust view-space gradient, no dome geometry and no horizon seam.
world = bpy.data.worlds.new("SkyWorld"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
wout = wn.nodes.new("ShaderNodeOutputWorld")
wbg = wn.nodes.new("ShaderNodeBackground"); wbg.inputs["Strength"].default_value = 1.0
wgeo = wn.nodes.new("ShaderNodeNewGeometry")
wsep = wn.nodes.new("ShaderNodeSeparateXYZ")
wmap = wn.nodes.new("ShaderNodeMapRange")
wmap.inputs["From Min"].default_value = -0.35; wmap.inputs["From Max"].default_value = 0.85
try: wmap.clamp = True
except Exception: pass
wramp = wn.nodes.new("ShaderNodeValToRGB")
wramp.color_ramp.elements[0].position = 0.10; wramp.color_ramp.elements[0].color = (0.22, 0.14, 0.34, 1)
_e = wramp.color_ramp.elements.new(0.33); _e.color = (1.0, 0.55, 0.27, 1)
_e = wramp.color_ramp.elements.new(0.50); _e.color = (0.93, 0.44, 0.47, 1)
_e = wramp.color_ramp.elements.new(0.62); _e.color = (0.33, 0.26, 0.60, 1)
wramp.color_ramp.elements[1].position = 0.86; wramp.color_ramp.elements[1].color = (0.05, 0.07, 0.26, 1)
# Incoming points scene->camera, so negate Z to get the ray's own up-component
wneg = wn.nodes.new("ShaderNodeMath"); wneg.operation = "MULTIPLY"; wneg.inputs[1].default_value = -1.0
wn.links.new(wgeo.outputs["Incoming"], wsep.inputs["Vector"])
wn.links.new(wsep.outputs["Z"], wneg.inputs[0])
wn.links.new(wneg.outputs[0], wmap.inputs[0])
wn.links.new(wmap.outputs[0], wramp.inputs["Fac"])
wn.links.new(wramp.outputs["Color"], wbg.inputs["Color"])
wn.links.new(wbg.outputs[0], wout.inputs["Surface"])

# sun glow: bright core disc + tight radial halo, both billboarded to the camera
glow_m = mat("SunCore", (1.0, 0.62, 0.25), 0.4, emission=(1.0, 0.55, 0.18), es=5.0)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=3.1, fill_type="NGON", location=tuple(SUN_POS))
o = bpy.context.object; finish(o, glow_m)
o.rotation_euler = (SUN_POS - CAM_POS).to_track_quat("-Z", "Y").to_euler()
img = bpy.data.images.new("HaloTex", 256, 256, alpha=True)
px = []
for yy in range(256):
    for xx in range(256):
        d = math.hypot(xx - 127.5, yy - 127.5) / 127.5
        a = max(0.0, 1.0 - d) ** 3.2
        px += [1.0, 0.62, 0.28, a]
img.pixels = px
img.alpha_mode = "STRAIGHT"
img.update()
halo_m = bpy.data.materials.new("SunHalo"); halo_m.use_nodes = True; halo_m.surface_render_method = "DITHERED"
hn = halo_m.node_tree
hemit = hn.nodes.new("ShaderNodeEmission"); hemit.inputs["Color"].default_value = (1.0, 0.58, 0.22, 1); hemit.inputs["Strength"].default_value = 0.95
htex = hn.nodes.new("ShaderNodeTexImage"); htex.image = img
hout = hn.nodes["Material Output"]
mixn = hn.nodes.new("ShaderNodeMixShader")
trans = hn.nodes.new("ShaderNodeBsdfTransparent")
hn.links.new(htex.outputs["Alpha"], mixn.inputs["Fac"])
hn.links.new(trans.outputs[0], mixn.inputs[1]); hn.links.new(hemit.outputs[0], mixn.inputs[2])
hn.links.new(mixn.outputs[0], hout.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=30, location=tuple(SUN_POS))
o = bpy.context.object; o.data.materials.append(halo_m)
o.rotation_euler = (SUN_POS - CAM_POS).to_track_quat("-Z", "Y").to_euler()

# ================================================================ LIGHTS
# strong warm SUN lamp raking in from behind-left of the whale (rim + cloud tops)
sd = bpy.data.lights.new("SunKey", "SUN"); sd.energy = 4.2; sd.color = (1.0, 0.62, 0.34); sd.angle = 0.6
so = bpy.data.objects.new("SunKey", sd); scene.collection.objects.link(so)
so.rotation_euler = (Vector((0, 5, 18)) - Vector((-38, 42, 40))).to_track_quat("-Z", "Y").to_euler()
def area(name, loc, energy, size, color):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = "DISK"; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 8, 20)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
area("RimWarm", (-34, 30, 48), 2800, 9, (1.0, 0.66, 0.38))     # hot rim from behind the whale
area("FillCool", (30, -34, 16), 1150, 8, (0.52, 0.68, 1.0))    # cool fill from camera side
area("CharKey", (22, -30, 20), 850, 5, (1.0, 0.80, 0.60))      # gentle warm key on Shizuku
d = bpy.data.lights.new("EyeGlow", "POINT"); d.energy = 180; d.color = (1.0, 0.72, 0.32)
o = bpy.data.objects.new("EyeGlow", d); scene.collection.objects.link(o); o.location = tuple(eye_c + dir_cam * 2.2)

# ================================================================ CAMERA + DOF
cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 19
cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
cam.location = tuple(CAM_POS)
cam.rotation_euler = (CAM_TGT - CAM_POS).to_track_quat("-Z", "Y").to_euler()
cam_data.dof.use_dof = True
cam_data.dof.focus_object = grp
try:
    cam_data.dof.aperture_fstop = 4.2
    cam_data.dof.aperture_blades = 6
except Exception:
    pass

# ================================================================ COMPOSITOR (Glare + vignette)
scene.use_nodes = True
ct = scene.node_tree; ct.nodes.clear()
rl = ct.nodes.new("CompositorNodeRLayers")
glare = ct.nodes.new("CompositorNodeGlare")
try: glare.glare_type = "FOG_GLOW"
except Exception: pass
try: glare.quality = "HIGH"
except Exception: pass
for sock, val in (("Mix", 0.35), ("Threshold", 0.75), ("Strength", 1.15), ("Size", 7)):
    try: glare.inputs[sock].default_value = val
    except Exception: pass
comp = ct.nodes.new("CompositorNodeComposite")
# NOTE: a compositor ellipse-mask vignette was tried and removed — at preview
# scale its transition band printed as a visible oval artefact in the sky.
# Glare only; the frame's natural light falloff carries the edges.
try:
    ct.links.new(rl.outputs["Image"], glare.inputs[0])
    ct.links.new(glare.outputs[0], comp.inputs[0])
except Exception:
    ct.links.new(rl.outputs["Image"], comp.inputs[0])

# ================================================================ RENDER
scene.render.engine = "CYCLES"
scene.cycles.use_denoising = True
scene.cycles.device = "CPU"
scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "High Contrast"
scene.view_settings.exposure = 0.3
if PREVIEW:
    scene.cycles.samples = 20
    scene.render.resolution_x = 640; scene.render.resolution_y = 360
    scene.render.filepath = "/tmp/kv_preview.png"
else:
    scene.cycles.samples = 96
    scene.render.resolution_x = 1280; scene.render.resolution_y = 720
    scene.render.filepath = os.path.join(OUT, "keyvisual.png")
scene.render.image_settings.file_format = "PNG"
if not PREVIEW:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "keyvisual.blend"))
bpy.ops.render.render(write_still=True)
print("KEYVISUAL V3 DONE", "PREVIEW" if PREVIEW else "FINAL")
