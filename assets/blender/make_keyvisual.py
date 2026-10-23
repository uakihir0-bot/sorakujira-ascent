"""Key visual for SORAKUJIRA — round 5.1 (v5.2 models, profile reshoot).

Appends the CURRENT v5.2 models (sorakujira.blend / shizuku.blend: node-baked
4K skin, carved head, iris+cornea eye assembly, throat-only pleats; SSS
shizuku) untouched, and keeps the v5 set dressing: world-shader sky with
nebula/starfield, warm sun + halo, island chain, fine foreground cloud
puffs, crystals, birds, Fog Glow, DOF f/4.2 on Shizuku. FRAMING (v5.1):
the v5 camera sat below-front of the head and framed the melon dome from
underneath. The reshoot is a 3/4 SIDE view — the camera sits roughly
level with the head, off its front-side; the head's local basis is mapped
so the snout tangent points screen-LEFT in profile (slightly down,
slightly toward camera) while the +e2 R-eye side faces the camera, so we
read snout profile, the large golden eye, the jaw-hugging mouth line and
the melon as a gentle forehead, with the body arcing down-right into the
cloud sea. The camera-side eye is probed to NDC (0.36, 0.66). Rim light
rakes the head's top contour and a soft camera-side FaceFill keeps a
gradient on the face.

Env KV_MODE=preview renders a fast 640x360 check to /tmp/kv_preview.png.
Final: 1280x720, 96 samples -> assets/keyvisual.png + keyvisual.blend.
"""
import bpy, math, os, random
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.environ.get("KV_MODE") == "preview"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
random.seed(11)

CAM_POS = Vector((16.0, -38.0, 16.0))
CAM_TGT = Vector((0.0, -2.0, 15.0))
CHAR_POS = Vector((13.0, -11.0, 4.5))           # feet of Shizuku (islet top, foreground)
SUN_POS = Vector((-66.0, 16.0, 26.0))          # low sun beside the whale's head

# ------------------------------------------------------------------ append models
def append_objects(path):
    with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
        data_to.objects = list(data_from.objects)
    objs = []
    for o in data_to.objects:
        if o is not None:
            bpy.context.scene.collection.objects.link(o)
            objs.append(o)
    return objs

whale_objs = append_objects(os.path.join(OUT, "sorakujira.blend"))
shizuku_objs = append_objects(os.path.join(OUT, "shizuku.blend"))
whale = bpy.data.objects["Sorakujira"]
shizuku = bpy.data.objects["Shizuku"]
skin_tex = bpy.data.images.get("SkinTex")
print("KV4 CHECK whale objects:", len(whale_objs), "| shizuku objects:", len(shizuku_objs),
      "| SkinTex packed:", bool(skin_tex and skin_tex.packed_file))

# whale: transform is NOT set here — it is solved analytically in the POSE
# section below (after the camera exists) so the face lands in 3/4 view
# with the camera-side eye at NDC (0.34, 0.61).

# Shizuku: the real model, facing the camera (-Y), chin tipped up at the whale.
shizuku.location = tuple(CHAR_POS)
shizuku.scale = (6.8, 6.8, 6.8)
shizuku.rotation_euler = (math.radians(-14), 0.0, math.radians(15))

# ---------------------------------------------------------------- materials (set dressing only)
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

CLOUD_M = mat("Cloud", (1.02, 0.95, 0.88), 0.95)
CLOUD_M2 = mat("CloudShadow", (0.78, 0.74, 0.90), 0.95)
ROCK_M = mat("Rock", (0.32, 0.27, 0.36), 0.85)
MOSS_M = mat("MossTop", (0.48, 0.70, 0.50), 0.8)
CRY_M = mat("Crystal", (0.58, 0.45, 0.99), 0.18, emission=(0.52, 0.36, 1.0), es=1.1, alpha=0.94)
CRYC_M = mat("CrystalCyan", (0.40, 0.85, 1.0), 0.18, emission=(0.3, 0.75, 1.0), es=1.1, alpha=0.94)
DOT_M = mat("Dot", (0.45, 0.95, 1.0), 0.4, emission=(0.4, 0.9, 1.0), es=2.2)
DOTG_M = mat("DotGold", (1.0, 0.8, 0.4), 0.4, emission=(1.0, 0.72, 0.3), es=2.0)
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

# ================================================================ CLOUD SEA
for k in range(150):
    x = random.uniform(-42, 42); y = random.uniform(-26, 38)
    z = random.uniform(-4.0, 3.2) - 0.012 * (x * x) * 0.02
    s = random.uniform(2.2, 8.5)
    sphere(f"Cloud{k}", (x, y, z), (s, s * 0.80, s * 0.50),
           CLOUD_M if k % 3 else CLOUD_M2, seg=16, rings=12)
# far cloud clusters resting low on the horizon behind the whale
for k in range(10):
    x = random.uniform(-44, 34); y = random.uniform(28, 48)
    z = random.uniform(-2, 6); s = random.uniform(4.0, 8.0)
    sphere(f"HiCloud{k}", (x, y, z), (s, s * 0.72, s * 0.45), CLOUD_M, seg=12, rings=9)
# smaller, more numerous puffs in the near foreground base (below the hero
# islet) — fine-grained cloud texture instead of a marshmallow wall
for k in range(18):
    x = random.uniform(-40, 40); y = random.uniform(-34, -12)
    z = random.uniform(-6.0, -2.5); s = random.uniform(3.2, 6.8)
    sphere(f"FgCloud{k}", (x, y, z), (s, s * 0.82, s * 0.48),
           CLOUD_M if k % 3 else CLOUD_M2, seg=16, rings=12)
# a soft cloud collar cradling the whale where its body dives into the sea
for k in range(22):
    a = random.uniform(0, math.tau); rr = random.uniform(16, 30)
    x = 2.0 + math.cos(a) * rr; y = 6.0 + math.sin(a) * rr * 0.8
    z = random.uniform(-3.5, 1.5); s = random.uniform(3.0, 7.5)
    sphere(f"Collar{k}", (x, y, z), (s, s * 0.8, s * 0.5),
           CLOUD_M if k % 3 else CLOUD_M2, seg=14, rings=10)

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

islet(CHAR_POS.x, CHAR_POS.y, CHAR_POS.z, 5.2)                    # hero islet
islet(7.5, -2.0, 9.5, 2.3)                                        # chain toward the whale
islet(3.0, 7.0, 14.0, 1.8)
islet(-4.0, 13.0, 19.5, 1.4, with_crystal=False)
islet(12.0, 11.0, 14.5, 1.3)

# ================================================================ CRYSTALS / SPARKS / BIRDS
def crystal(loc, h, r, tilt, m=CRY_M):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, radius2=0.0, depth=h, location=loc)
    o = bpy.context.object; finish(o, m); o.rotation_euler = tilt
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.0, radius2=r * 0.9, depth=h * 0.42,
                                    location=(loc[0], loc[1], loc[2] - h * 0.68))
    o2 = bpy.context.object; finish(o2, m); o2.rotation_euler = tilt
crystal((4.0, 8.0, 20.0), 4.6, 0.9, (math.radians(12), 0, math.radians(-8)))
crystal((17.5, 3.0, 23.0), 5.4, 1.05, (math.radians(-8), 0, math.radians(10)), CRYC_M)
crystal((-20.0, 20.0, 42.0), 4.8, 0.95, (math.radians(6), 0, math.radians(14)))
crystal((CHAR_POS.x + 4.6, CHAR_POS.y + 1.6, CHAR_POS.z + 2.4), 2.4, 0.55, (math.radians(-10), 0, math.radians(-12)), CRYC_M)
crystal((10.5, 3.0, 15.0), 3.2, 0.7, (math.radians(-14), 0, math.radians(6)))
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

# ================================================================ SKY (world shader, enriched)
# Ray direction d = -Incoming (Incoming points scene->camera). The gradient
# ramp is driven by elevation, then enriched by: sun-azimuth warmth near the
# horizon, low-frequency nebula noise (hue + brightness) and a fine Voronoi
# starfield masked to the upper sky. No dome geometry, no horizon seam.
world = bpy.data.worlds.new("SkyWorld"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
wout = wn.nodes.new("ShaderNodeOutputWorld")
wbg = wn.nodes.new("ShaderNodeBackground"); wbg.inputs["Strength"].default_value = 1.0
wgeo = wn.nodes.new("ShaderNodeNewGeometry")
wneg = wn.nodes.new("ShaderNodeVectorMath"); wneg.operation = "SCALE"
wneg.inputs["Scale"].default_value = -1.0
wn.links.new(wgeo.outputs["Incoming"], wneg.inputs["Vector"])
D = wneg.outputs["Vector"]

def wmath(op, a=None, b=None, clamp=False):
    n = wn.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    if a is not None:
        if isinstance(a, (int, float)): n.inputs[0].default_value = a
        else: wn.links.new(a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): n.inputs[1].default_value = b
        else: wn.links.new(b, n.inputs[1])
    return n.outputs[0]

def wmaprange(v, fmin, fmax, tmin, tmax):
    n = wn.nodes.new("ShaderNodeMapRange")
    n.inputs["From Min"].default_value = fmin; n.inputs["From Max"].default_value = fmax
    n.inputs["To Min"].default_value = tmin; n.inputs["To Max"].default_value = tmax
    try: n.clamp = True
    except Exception: pass
    wn.links.new(v, n.inputs["Value"])
    return n.outputs["Result"]

def wmix(mode, fac, c1, c2):
    n = wn.nodes.new("ShaderNodeMixRGB"); n.blend_type = mode
    if isinstance(fac, (int, float)): n.inputs["Fac"].default_value = fac
    else: wn.links.new(fac, n.inputs["Fac"])
    if isinstance(c1, tuple): n.inputs["Color1"].default_value = (*c1, 1.0)
    else: wn.links.new(c1, n.inputs["Color1"])
    if isinstance(c2, tuple): n.inputs["Color2"].default_value = (*c2, 1.0)
    else: wn.links.new(c2, n.inputs["Color2"])
    return n.outputs["Color"]

wsep = wn.nodes.new("ShaderNodeSeparateXYZ"); wn.links.new(D, wsep.inputs["Vector"])
t = wmaprange(wsep.outputs["Z"], -0.30, 0.95, 0.0, 1.0)      # elevation 0..1
wramp = wn.nodes.new("ShaderNodeValToRGB")
_ramp = [(0.00, (0.10, 0.06, 0.22)), (0.14, (0.42, 0.16, 0.36)), (0.24, (1.05, 0.38, 0.10)),
         (0.32, (0.94, 0.47, 0.40)), (0.45, (0.42, 0.29, 0.63)), (0.62, (0.11, 0.15, 0.41)),
         (0.80, (0.03, 0.05, 0.23)), (1.00, (0.008, 0.016, 0.10))]
wramp.color_ramp.elements[0].position = _ramp[0][0]; wramp.color_ramp.elements[0].color = (*_ramp[0][1], 1)
wramp.color_ramp.elements[1].position = _ramp[-1][0]; wramp.color_ramp.elements[1].color = (*_ramp[-1][1], 1)
for pos, col in _ramp[1:-1]:
    _e = wramp.color_ramp.elements.new(pos); _e.color = (*col, 1)
wn.links.new(t, wramp.inputs["Fac"])
sky = wramp.outputs["Color"]

# --- sun-azimuth warmth: looking toward the sun warms the horizon band
_sun_h = Vector((SUN_POS.x - CAM_POS.x, SUN_POS.y - CAM_POS.y, 0.0)); _sun_h.normalize()
dot = wmath("ADD",
            wmath("MULTIPLY", wsep.outputs["X"], _sun_h.x),
            wmath("MULTIPLY", wsep.outputs["Y"], _sun_h.y))
warm01 = wmaprange(dot, -0.85, 0.85, 0.0, 1.0)
band = wmath("SUBTRACT", 1.0,
             wmath("DIVIDE", wmath("ABSOLUTE", wmath("SUBTRACT", t, 0.30)), 0.38), clamp=True)
warmfac = wmath("MULTIPLY", wmath("MULTIPLY", warm01, band), 0.80)
sky = wmix("MIX", warmfac, sky, wmix("MULTIPLY", 1.0, sky, (1.32, 1.03, 0.70)))

# --- nebula noise: hue drift + brightness variation, mostly in the upper sky
wscaled = wn.nodes.new("ShaderNodeVectorMath"); wscaled.operation = "SCALE"
wscaled.inputs["Scale"].default_value = 2.2; wn.links.new(D, wscaled.inputs["Vector"])
wnoise = wn.nodes.new("ShaderNodeTexNoise")
wnoise.inputs["Detail"].default_value = 3.0; wnoise.inputs["Roughness"].default_value = 0.7
wn.links.new(wscaled.outputs["Vector"], wnoise.inputs["Vector"])
nf = wnoise.outputs["Fac"]
upper = wmaprange(t, 0.35, 0.80, 0.0, 1.0)
nebfac = wmath("MULTIPLY", wmaprange(nf, 0.30, 0.78, 0.0, 0.50), upper)
sky = wmix("MIX", nebfac, sky, wmix("MULTIPLY", 1.0, sky, (0.82, 0.90, 1.30)))
sky = wmix("MULTIPLY", 1.0, sky, wmaprange(nf, 0.20, 0.90, 0.90, 1.09))

# --- fine starfield: Voronoi cell-centre points, upper sky only
wstar = wn.nodes.new("ShaderNodeVectorMath"); wstar.operation = "SCALE"
wstar.inputs["Scale"].default_value = 38.0; wn.links.new(D, wstar.inputs["Vector"])
wvor = wn.nodes.new("ShaderNodeTexVoronoi")
try: wvor.feature = "F1"
except Exception: pass
wn.links.new(wstar.outputs["Vector"], wvor.inputs["Vector"])
core = wmath("MULTIPLY",
             wmath("SUBTRACT", 0.012, wvor.outputs["Distance"], clamp=True), 160.0, clamp=True)
core = wmath("POWER", core, 1.5)
starmask = wmaprange(t, 0.36, 0.62, 0.0, 1.0)
wsepc = wn.nodes.new("ShaderNodeSeparateRGB"); wn.links.new(wvor.outputs["Color"], wsepc.inputs["Image"])
vary = wmaprange(wsepc.outputs["R"], 0.0, 1.0, 0.35, 1.0)
star_i = wmath("MULTIPLY", wmath("MULTIPLY", core, starmask), vary)
star_col = wmix("MULTIPLY", 1.0, (0.85, 0.92, 1.0), star_i)
sky = wmix("ADD", 1.0, sky, star_col)

wn.links.new(sky, wbg.inputs["Color"])
wn.links.new(wbg.outputs[0], wout.inputs["Surface"])

# ================================================================ SUN GLOW (warmer, wider)
glow_m = mat("SunCore", (1.0, 0.47, 0.10), 0.4, emission=(1.0, 0.40, 0.05), es=7.6)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=3.4, fill_type="NGON", location=tuple(SUN_POS))
o = bpy.context.object; finish(o, glow_m)
o.rotation_euler = (SUN_POS - CAM_POS).to_track_quat("-Z", "Y").to_euler()
img = bpy.data.images.new("HaloTex", 256, 256, alpha=True)
px = []
for yy in range(256):
    for xx in range(256):
        d = math.hypot(xx - 127.5, yy - 127.5) / 127.5
        a = max(0.0, 1.0 - d) ** 2.4
        px += [1.0, 0.54, 0.17, a]
img.pixels = px
img.alpha_mode = "STRAIGHT"
img.pack()                                   # pack BEFORE saving; colorspace AFTER pack
img.colorspace_settings.name = "Non-Color"
halo_m = bpy.data.materials.new("SunHalo"); halo_m.use_nodes = True; halo_m.surface_render_method = "DITHERED"
hn = halo_m.node_tree
hemit = hn.nodes.new("ShaderNodeEmission"); hemit.inputs["Color"].default_value = (1.0, 0.44, 0.08, 1); hemit.inputs["Strength"].default_value = 1.55
htex = hn.nodes.new("ShaderNodeTexImage"); htex.image = img
hout = hn.nodes["Material Output"]
mixn = hn.nodes.new("ShaderNodeMixShader")
trans = hn.nodes.new("ShaderNodeBsdfTransparent")
hn.links.new(htex.outputs["Alpha"], mixn.inputs["Fac"])
hn.links.new(trans.outputs[0], mixn.inputs[1]); hn.links.new(hemit.outputs[0], mixn.inputs[2])
hn.links.new(mixn.outputs[0], hout.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=42, location=tuple(SUN_POS))
o = bpy.context.object; o.data.materials.append(halo_m)
o.rotation_euler = (SUN_POS - CAM_POS).to_track_quat("-Z", "Y").to_euler()

# ================================================================ LIGHTS
sd = bpy.data.lights.new("SunKey", "SUN"); sd.energy = 4.4; sd.color = (1.0, 0.58, 0.30); sd.angle = 0.6
so = bpy.data.objects.new("SunKey", sd); scene.collection.objects.link(so)
so.rotation_euler = (Vector((0, 8, 20)) - SUN_POS).to_track_quat("-Z", "Y").to_euler()
def area(name, loc, energy, size, color):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = "DISK"; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 8, 20)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
area("RimWarm", (-38, 26, 42), 3800, 9, (1.0, 0.62, 0.34))     # hot rim from behind the whale's head
area("FillCool", (30, -34, 16), 1150, 8, (0.52, 0.68, 1.0))    # cool fill from camera side
area("CharKey", (24, -33, 18), 900, 5, (1.0, 0.80, 0.60))      # gentle warm key on Shizuku
# warm glint for the eye — created here, positioned in the POSE section
# once the whale transform is solved.
d = bpy.data.lights.new("EyeGlow", "POINT"); d.energy = 340; d.color = (1.0, 0.72, 0.32)
o = bpy.data.objects.new("EyeGlow", d); scene.collection.objects.link(o)

# ================================================================ CAMERA + DOF
cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 19
cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
cam.location = tuple(CAM_POS)
cam.rotation_euler = (CAM_TGT - CAM_POS).to_track_quat("-Z", "Y").to_euler()
cam_data.dof.use_dof = True
cam_data.dof.focus_object = shizuku
try:
    cam_data.dof.aperture_fstop = 4.2
    cam_data.dof.aperture_blades = 6
except Exception:
    pass

# ================================================================ POSE (analytic solve)
# The whale's face is the +e2 lateral side of the head (eye R, mouth line).
# Local head basis from the model's own loft math: f = tangent at the
# snout station, s = +e2 (R-eye side), u = f x s (~belly). We rotate the
# whale so that in world space f points right/down/toward camera on the
# eye-line to Shizuku (a true 3/4 face read), roll +25 deg around f so the
# coil arcs away left and dives into the cloud sea, then solve the
# location iteratively until EyeballR probes to NDC (0.34, 0.67).
from bpy_extras.object_utils import world_to_camera_view

def wpath(t):
    ang = t * math.radians(300)
    r = 13.0 * (1.0 - 0.45 * t)
    return Vector((r * math.cos(ang), r * math.sin(ang), 4.0 + t * 60.0))

def wframe(t):
    c = wpath(t)
    e = 0.0015
    tan = (wpath(min(1.0, t + e)) - wpath(max(0.0, t - e)))
    tan.normalize()
    ang = t * math.radians(300)
    radial = Vector((math.cos(ang), math.sin(ang), 0))
    e1 = radial - tan * radial.dot(tan)
    e1.normalize()
    e2v = tan.cross(e1); e2v.normalize()
    return c, tan, e1, e2v

SIGMA = 2.3
EYE_TGT = Vector((float(os.environ.get("KV_EYEX", 0.36)),
                  float(os.environ.get("KV_EYEY", 0.66))))
head_l, _ht, _he1, he2_l = wframe(0.925)          # head centre (eye station)
_c1, tan1_l, _e1, _e2 = wframe(1.0)
snout_l = _c1 + tan1_l * 2.7
f_l = tan1_l.normalized()
u_l = f_l.cross(he2_l).normalized()
s_l = u_l.cross(f_l).normalized()                  # ~+e2, R-eye side
eyeR_l = bpy.data.objects["EyeballR"].matrix_world.translation.copy()

# v5.1: head centre placed explicitly ~53 units from the camera (the
# first profile pass at ~33 units filled the whole frame with the head
# and cropped Shizuku and the body arc out entirely). At this depth the
# head spans roughly a third of the frame height, the coil can arc
# down-right into the cloud sea, and Shizuku stays the near foreground.
H0 = Vector((-14.0, 10.0, 30.0))

scene.render.resolution_x = 1280; scene.render.resolution_y = 720
Rc = cam.matrix_world.to_3x3()
cam_right = Rc @ Vector((1, 0, 0))
cam_up = Rc @ Vector((0, 1, 0))
V = (CAM_POS - H0).normalized()                    # head -> camera
# PROFILE basis: the snout tangent f points screen-LEFT (the head reads
# in profile), tipped slightly down and slightly toward the camera for
# the 3/4 read; the R-eye side s faces the camera. KV_FRONT / KV_ROLL
# exist only for preview tuning; the committed defaults are final.
FRONT = float(os.environ.get("KV_FRONT", 0.42))
ROLL = math.radians(float(os.environ.get("KV_ROLL", 50)))
f_w = (cam_right * -1.0 + cam_up * -0.16 + V * FRONT).normalized()
_s0 = V + cam_up * 0.06 + cam_right * 0.10
s_w0 = (_s0 - f_w * _s0.dot(f_w)).normalized()
u_w0 = f_w.cross(s_w0).normalized()
s_w = (s_w0 * math.cos(ROLL) + u_w0 * math.sin(ROLL)).normalized()
u_w = f_w.cross(s_w).normalized()
Lmat = Matrix(((f_l.x, s_l.x, u_l.x), (f_l.y, s_l.y, u_l.y), (f_l.z, s_l.z, u_l.z)))
Wmat = Matrix(((f_w.x, s_w.x, u_w.x), (f_w.y, s_w.y, u_w.y), (f_w.z, s_w.z, u_w.z)))
R1 = Wmat @ Lmat.transposed()
whale.rotation_euler = R1.to_euler()
whale.scale = (SIGMA, SIGMA, SIGMA)

b1 = cam_right.copy()
b2 = V.cross(b1).normalized()
H = H0.copy()
for _ in range(4):
    whale.location = H - (R1 @ (head_l * SIGMA))
    bpy.context.view_layer.update()
    E = whale.matrix_world @ eyeR_l
    pr = world_to_camera_view(scene, cam, E)
    depth = (E - CAM_POS).dot((CAM_TGT - CAM_POS).normalized())
    fw_ = 2 * depth * (18.0 / 19.0)
    fh_ = fw_ * 720.0 / 1280.0
    H += b1 * (-(pr.x - EYE_TGT.x) * fw_) + b2 * (-(pr.y - EYE_TGT.y) * fh_)
whale.location = H - (R1 @ (head_l * SIGMA))
bpy.context.view_layer.update()
_pe = world_to_camera_view(scene, cam, whale.matrix_world @ eyeR_l)
_ps = world_to_camera_view(scene, cam, whale.matrix_world @ snout_l)
eye_w = bpy.data.objects["EyeballR"].matrix_world.translation
print("KV42 CHECK eye NDC:", (round(_pe.x, 3), round(_pe.y, 3)),
      "| snout NDC:", (round(_ps.x, 3), round(_ps.y, 3)),
      "| head world:", tuple(round(v, 1) for v in (whale.matrix_world @ head_l)))
for _nm in ("PecFinR", "MouthR", "Blowhole"):
    _o = bpy.data.objects[_nm]
    _c = sum((_o.matrix_world @ Vector(cn) for cn in _o.bound_box), Vector()) / 8
    _p = world_to_camera_view(scene, cam, _c)
    print("KV51 CHECK", _nm, "NDC:", (round(_p.x, 3), round(_p.y, 3)))

# head lighting, re-aimed for the new pose: a gentle warm rim raking the
# top contour from behind/above the head, and a soft camera-side fill so
# the face keeps a gradient (countershading sweep) instead of flat dark.
Hw = whale.matrix_world @ head_l
dorsal_w = (R1 @ (-u_l)).normalized()              # ~+e1, out of the back
rim = bpy.data.objects["RimWarm"]
rim.data.energy = 3000; rim.data.size = 11
rim.location = tuple(Hw + dorsal_w * 14 - V * 30 + cam_up * 6)
rim.rotation_euler = (Hw - rim.location).to_track_quat("-Z", "Y").to_euler()
fd = bpy.data.lights.new("FaceFill", "AREA"); fd.energy = 1250; fd.shape = "DISK"
fd.size = 14; fd.color = (0.95, 0.82, 0.70)
fo = bpy.data.objects.new("FaceFill", fd); scene.collection.objects.link(fo)
fo.location = tuple(Hw + V * 26 + cam_right * 6 - cam_up * 2)
fo.rotation_euler = (Hw - fo.location).to_track_quat("-Z", "Y").to_euler()
eg = bpy.data.objects["EyeGlow"]
eg.location = tuple(eye_w + (CAM_POS - eye_w).normalized() * 3.6 + Vector((0, 0, 0.5)))
print("KV42 CHECK eye world:", tuple(round(v, 1) for v in eye_w))

# ================================================================ COMPOSITOR (Fog Glow)
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
print("KEYVISUAL V5 DONE", "PREVIEW" if PREVIEW else "FINAL")
