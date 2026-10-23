"""Shizuku v4 - teardrop spirit player character for SORAKUJIRA.

v4 fixes over v3 (face, gold-rimmed core and side profile kept - they
worked; from dead front the fins still read as rabbit ears):
- Fin roots rotated ~20 deg toward the back of the body; bezier pushed
  laterally so the front silhouette bows OUTWARD like a swept crest
  framing the head, tips droop a touch lower than the root line.
- Pink -> pale gradient strengthened (richer pink base, near-white cyan
  tip) and the fin material gains a faint vertex-colour emission so the
  bright tips read slightly translucent.
- Slight saturation lift: body belly/mid gradient and cheeks richer,
  still pastel.
Origin: bottom-center of body. Body height ~1.2 (fins excluded). Facing -Y.
Saves shizuku.blend and exports shizuku.glb (modifiers applied on export).
"""
import bpy, math, os
from mathutils import Vector, Quaternion

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # assets/
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, roughness=0.35, emission=None, es=0.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metal
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = es
    return m

CORE_M  = mat("GlowCore", (0.35, 0.85, 1.00), 0.3, emission=(0.30, 0.80, 1.00), es=3.0)
CORE2_M = mat("CoreInner", (0.80, 0.98, 1.00), 0.2, emission=(0.65, 0.95, 1.00), es=4.5)
RIM_M   = mat("CoreRim", (0.85, 0.62, 0.25), 0.28, metal=0.9)
EYE_M   = mat("Eye", (0.02, 0.02, 0.04), 0.10)
IRIS_M  = mat("Iris", (0.35, 0.18, 0.05), 0.25, emission=(0.20, 0.08, 0.01), es=0.3)
PUPIL_M = mat("Pupil", (0.0, 0.0, 0.0), 0.15)
HL_M    = mat("Highlight", (1, 1, 1), 0.15, emission=(1, 1, 1), es=0.7)
CHEEK_M = mat("Cheek", (1.00, 0.50, 0.62), 0.5)
CREAM_M = mat("Cream", (1.00, 0.90, 0.76), 0.5)
MOUTH_M = mat("Mouth", (0.05, 0.03, 0.05), 0.4)

def vc_mat(name, roughness=0.38, glow=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
    bsdf = nt.nodes["Principled BSDF"]
    nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    if glow > 0.0:   # faint self-glow from the same colours: bright tips
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = glow
    return m
BODY_VC = vc_mat("ShizukuBodyVC", roughness=0.22)
FIN_VC = vc_mat("RibbonFinVC", glow=0.16)
ARM_VC = vc_mat("ArmFinVC", roughness=0.4)

def finish(obj, material, smooth=True):
    if material: obj.data.materials.append(material)
    if smooth and hasattr(obj.data, "polygons"):
        for p in obj.data.polygons: p.use_smooth = True
    return obj

def sphere(name, loc, scale, material, seg=24, rings=18):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    return finish(o, material)

def lerp3(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def smooth01(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

# ---- teardrop body: Catmull-Rom sampled lathe profile ----
CTRL = [(0.001, 0.00), (0.16, 0.01), (0.30, 0.06), (0.42, 0.18), (0.475, 0.34),
        (0.485, 0.48), (0.46, 0.62), (0.415, 0.76), (0.345, 0.88), (0.25, 0.99),
        (0.15, 1.08), (0.06, 1.15), (0.001, 1.20)]
def catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t +
                        (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 +
                        (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3) for i in range(2))
profile = []
for i in range(len(CTRL) - 1):
    p0 = CTRL[max(0, i - 1)]; p1 = CTRL[i]; p2 = CTRL[i + 1]; p3 = CTRL[min(len(CTRL) - 1, i + 2)]
    for k in range(8):
        r, z = catmull(p0, p1, p2, p3, k / 8)
        profile.append((max(0.001, r), z))
profile.append(CTRL[-1])

def radius_at(z):
    best = profile[0]
    for r, zz in profile:
        if abs(zz - z) < abs(best[1] - z): best = (r, zz)
    return best[0]

# vertical gradient: ice-blue belly -> white crown
C_BELLY = (0.715, 0.845, 1.000)
C_MID   = (0.895, 0.940, 1.000)
C_CROWN = (0.975, 0.988, 1.000)
def body_color(z):
    if z < 0.55:
        return lerp3(C_BELLY, C_MID, smooth01(z / 0.55))
    return lerp3(C_MID, C_CROWN, smooth01((z - 0.55) / 0.45))

verts, faces, bcols = [], [], []
SEG = 48
for r, z in profile:
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        verts.append((r * math.cos(a), r * math.sin(a), z))
        bcols.append((*body_color(z), 1.0))
for j in range(len(profile) - 1):
    for i in range(SEG):
        a = j * SEG + i; b = j * SEG + (i + 1) % SEG
        faces.append((a, b, b + SEG, a + SEG))
mesh = bpy.data.meshes.new("BodyMesh"); mesh.from_pydata(verts, [], faces); mesh.update()
ca = mesh.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
for i, c in enumerate(bcols): ca.data[i].color = c
mesh.color_attributes.active = ca
body = bpy.data.objects.new("Body", mesh); bpy.context.collection.objects.link(body)
finish(body, BODY_VC)
sub = body.modifiers.new("Subsurf", "SUBSURF"); sub.levels = 1; sub.render_levels = 1

# ---- lofted ribbon builder (centers, widths, side dirs, vertex colours) ----
def ribbon(name, centers, widths, sides, c0, c1, thick, material):
    vs, cols, fs = [], [], []
    n = len(centers)
    for i in range(n):
        t = i / (n - 1)
        col = tuple(c0[k] + (c1[k] - c0[k]) * t for k in range(3))
        for sgn in (-1, 1):
            p = centers[i] + sides[i] * (widths[i] * 0.5 * sgn)
            vs.append(tuple(p)); cols.append((*col, 1.0))
    for i in range(n - 1):
        a = i * 2
        fs.append((a, a + 1, a + 3, a + 2))
    m = bpy.data.meshes.new(name + "Mesh"); m.from_pydata(vs, [], fs); m.update()
    ca = m.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for i, c in enumerate(cols): ca.data[i].color = c
    m.color_attributes.active = ca
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    mod = o.modifiers.new("Solid", "SOLIDIFY"); mod.thickness = thick; mod.offset = 0.0
    return finish(o, material)

def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (p0 * (u ** 3) + p1 * (3 * u * u * t) + p2 * (3 * u * t * t) + p3 * (t ** 3))
def cubic_tan(p0, p1, p2, p3, t):
    u = 1 - t
    return ((p1 - p0) * (3 * u * u) + (p2 - p1) * (6 * u * t) + (p3 - p2) * (3 * t * t))

PINK, CYAN = (0.99, 0.60, 0.76), (0.80, 0.94, 1.00)
# head fins: sweep up, curve back, droop at the tips; twisted ribbon plane
for s, nm in ((1, "R"), (-1, "L")):
    P0 = Vector((0.17 * s, 0.14, 1.00)); P1 = Vector((0.42 * s, 0.20, 1.30))
    P2 = Vector((0.64 * s, 0.48, 1.36)); P3 = Vector((0.52 * s, 0.78, 0.97))
    centers, widths, sides = [], [], []
    NF = 15
    for i in range(NF):
        t = i / (NF - 1)
        centers.append(cubic(P0, P1, P2, P3, t))
        w = 0.035 + 0.205 * (1 - t) ** 0.65 * (1 + 0.38 * math.sin(math.pi * min(1.0, t * 1.05)))
        widths.append(w)
        tan = cubic_tan(P0, P1, P2, P3, t); tan.normalize()
        sd = Vector((tan.y, -tan.x, 0.0))
        if sd.length < 1e-5: sd = Vector((0.0, -s, 0.0))
        sd.normalize()
        q = Quaternion(tan, math.radians(-74.0) * t * s)
        sides.append(q @ sd)
    ribbon(f"RibbonFin{nm}", centers, widths, sides, PINK, CYAN, 0.016, FIN_VC)
# small tail ribbon at the back-bottom
centers = [Vector((0, 0.30, 0.30)), Vector((0, 0.44, 0.225)), Vector((0, 0.55, 0.13))]
widths = [0.17, 0.12, 0.05]
sides = [Vector((1, 0, 0))] * 3
ribbon("TailFin", centers, widths, sides, (0.86, 0.92, 1.0), CYAN, 0.014, FIN_VC)

# ---- glowing core: smooth lens (~68% of v2) + bright inner + gold rim ----
sphere("GlowCore", (0, -0.445, 0.415), (0.119, 0.070, 0.146), CORE_M, seg=48, rings=32)
sphere("CoreInner", (0, -0.495, 0.415), (0.060, 0.030, 0.074), CORE2_M, seg=32, rings=24)
bpy.ops.mesh.primitive_torus_add(major_radius=0.117, minor_radius=0.013,
                                 major_segments=40, minor_segments=10,
                                 location=(0, -0.468, 0.415))
rim = bpy.context.object; rim.name = "CoreRim"
rim.rotation_mode = 'QUATERNION'
rim.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector((0, -0.99, -0.10)))
rim.scale = (0.92, 1.12, 1.0)
finish(rim, RIM_M)

# ---- face: layered eyes, cheeks, smile curve hugging the surface ----
for s, nm in ((1, "R"), (-1, "L")):
    x = 0.175 * s
    sphere(f"Eye{nm}", (x, -0.400, 0.740), (0.055, 0.030, 0.082), EYE_M)
    sphere(f"Iris{nm}", (x, -0.428, 0.745), (0.032, 0.014, 0.048), IRIS_M)
    sphere(f"Pupil{nm}", (x, -0.440, 0.745), (0.017, 0.009, 0.026), PUPIL_M)
    sphere(f"HL{nm}", (x - 0.017 * s, -0.440, 0.775), (0.015, 0.008, 0.022), HL_M)
    sphere(f"Cheek{nm}", (0.30 * s, -0.360, 0.600), (0.078, 0.042, 0.058), CHEEK_M)
# smile: shallow U arc on the body surface, clear space above the core
mpts = []
for k in range(9):
    x = -0.058 + 0.116 * (k / 8)
    z = 0.620 + 0.030 * (x / 0.058) ** 2
    r = radius_at(z)
    y = -math.sqrt(max(r * r - x * x, 0.0004)) - 0.004
    mpts.append((x, y, z))
cu = bpy.data.curves.new("MouthCurve", 'CURVE'); cu.dimensions = '3D'
cu.bevel_depth = 0.011; cu.bevel_resolution = 2
spl = cu.splines.new('POLY'); spl.points.add(len(mpts) - 1)
for p, co in zip(spl.points, mpts): p.co = (*co, 1.0)
mouth = bpy.data.objects.new("Mouth", cu); bpy.context.collection.objects.link(mouth)
mouth.data.materials.append(MOUTH_M)
bpy.context.view_layer.objects.active = mouth; mouth.select_set(True)
bpy.ops.object.convert(target='MESH'); mouth.select_set(False)

# ---- arm fins: mini lathe teardrops, ice -> pink tip, hugging the body ----
ARM_PROF = [(0.001, 0.00), (0.045, 0.02), (0.058, 0.09), (0.046, 0.18),
            (0.018, 0.25), (0.001, 0.29)]
def mini_lathe(name, prof, c0, c1, material, seg=20):
    vs, fs, cols = [], [], []
    for j, (r, h) in enumerate(prof):
        col = lerp3(c0, c1, j / (len(prof) - 1))
        for i in range(seg):
            a = 2 * math.pi * i / seg
            vs.append((r * math.cos(a), r * math.sin(a), h))
            cols.append((*col, 1.0))
    for j in range(len(prof) - 1):
        for i in range(seg):
            a = j * seg + i; b = j * seg + (i + 1) % seg
            fs.append((a, b, b + seg, a + seg))
    m = bpy.data.meshes.new(name + "Mesh"); m.from_pydata(vs, [], fs); m.update()
    ca = m.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for i, c in enumerate(cols): ca.data[i].color = c
    m.color_attributes.active = ca
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    return finish(o, material)

for s, nm in ((1, "R"), (-1, "L")):
    arm = mini_lathe(f"ArmFin{nm}", ARM_PROF, (0.76, 0.85, 0.99), (0.98, 0.56, 0.74), ARM_VC)
    arm.location = (0.44 * s, 0.03, 0.60)
    arm.scale = (1.0, 1.0, 1.25)
    q = Quaternion((0, 0, 1), -0.46 * s) @ Quaternion((1, 0, 0), math.radians(-160))
    arm.rotation_mode = 'QUATERNION'; arm.rotation_quaternion = q

# ---- little feet ----
sphere("FootL", (-0.20, -0.15, 0.040), (0.125, 0.165, 0.048), CREAM_M)
sphere("FootR", ( 0.20, -0.15, 0.040), (0.125, 0.165, 0.048), CREAM_M)

# ---- wrap up ----
root = bpy.data.objects.new("Shizuku", None); bpy.context.collection.objects.link(root)
for o in list(bpy.context.collection.objects):
    if o != root and o.parent is None:
        o.parent = root
dg = bpy.context.evaluated_depsgraph_get()
tot = sum(len(o.evaluated_get(dg).data.polygons) for o in bpy.context.collection.objects
          if o.type == 'MESH')
print("EVALUATED POLYGONS:", tot)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "shizuku.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "shizuku.glb"),
                          export_format="GLB", export_apply=True)
print("SHIZUKU V4 DONE")
