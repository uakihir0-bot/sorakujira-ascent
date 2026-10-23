"""Sorakujira - the colossal sky whale, game-ready stylized model.
Body: dense overlapping spheres along an upward helix (organic beaded form),
defined head at the top with a glowing eye, huge tail fins at the bottom,
pectoral + dorsal fins, emissive plankton dots. Total height ~60 units.
Saves sorakujira.blend and exports sorakujira.glb.
"""
import bpy, math, os, random

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(42)

def mat(name, color, roughness=0.55, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = emission_strength
    return m

# body gradient: deep indigo at tail -> luminous blue-violet at head
def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
TAIL_C, HEAD_C = (0.045, 0.09, 0.24), (0.16, 0.28, 0.55)
BODY_MS = [mat(f"WhaleBody{i}", lerp(TAIL_C, HEAD_C, i / 4), 0.5) for i in range(5)]
BELLY_M = mat("WhaleBelly", (0.62, 0.72, 0.90), 0.6)
FIN_M   = mat("WhaleFin", (0.10, 0.20, 0.45), 0.5)
EYE_M   = mat("WhaleEye", (1.0, 0.80, 0.35), 0.25, emission=(1.0, 0.72, 0.25), emission_strength=4.0)
DOT_M   = mat("Plankton", (0.45, 0.95, 1.0), 0.4, emission=(0.40, 0.90, 1.0), emission_strength=2.4)
DOT_M2  = mat("PlanktonGold", (1.0, 0.85, 0.45), 0.4, emission=(1.0, 0.80, 0.40), emission_strength=2.2)

def finish(obj, material):
    if material: obj.data.materials.append(material)
    if hasattr(obj.data, "polygons"):
        for p in obj.data.polygons: p.use_smooth = True
    return obj

def sphere(name, loc, scale, material, seg=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    return finish(o, material)

# ---- helix path: bottom (tail) -> top (head) ----
HEIGHT = 60.0
def path(t):
    ang = t * math.radians(300)          # gentle coil, ~300 degrees total
    r = 13.0 * (1.0 - 0.45 * t)
    return (r * math.cos(ang), r * math.sin(ang), 4.0 + t * HEIGHT), ang

N = 110
centers = []
for i in range(N):
    t = i / (N - 1)
    (x, y, z), ang = path(t)
    # body radius: slim tail, fat middle/head approach
    br = 1.6 + 4.6 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t)) ** 0.7
    if t > 0.92: br *= 1.0 - (t - 0.92) * 1.2
    centers.append((x, y, z, br, t))
    m = BODY_MS[min(4, int(t * 5))]
    sphere(f"Body{i}", (x, y, z), (br, br * 0.92, br * 1.02), m)
    # belly: lighter sphere tucked toward coil centre + down
    bx, by = x * 0.86, y * 0.86
    sphere(f"Belly{i}", (bx, by, z - br * 0.38), (br * 0.80, br * 0.74, br * 0.82), BELLY_M)

# ---- head at top end ----
hx, hy, hz, hbr, _ = centers[-1]
(x2, y2, z2), _ = path(0.97)
tangent = (hx - x2, hy - y2, hz - z2)
tl = math.sqrt(sum(c * c for c in tangent)); tangent = tuple(c / tl for c in tangent)
head_loc = (hx + tangent[0] * 2.0, hy + tangent[1] * 2.0, hz + tangent[2] * 2.0 + 0.6)
head = sphere("Head", head_loc, (5.0, 5.9, 4.7), BODY_MS[4], seg=32, rings=24)
# snout / jaw
sphere("Jaw", (head_loc[0] + tangent[0] * 2.6, head_loc[1] + tangent[1] * 2.6, head_loc[2] - 2.6),
       (4.0, 4.8, 2.2), BELLY_M, seg=32, rings=24)
# the great glowing eye - placed on the front-left of the head, plus a smaller right one
eye_pos = (head_loc[0] + 4.7, head_loc[1] - 2.2, head_loc[2] + 1.4)
sphere("EyeGreat", eye_pos, (1.15, 1.15, 1.15), EYE_M, seg=24, rings=16)
sphere("EyeSmall", (head_loc[0] - 4.8, head_loc[1] - 1.8, head_loc[2] + 1.2), (0.65, 0.65, 0.65), EYE_M, seg=24, rings=16)
# blowhole crown: small emissive dots ring on top of head handled by plankton pass

# ---- tail fins at bottom end (huge, flattened, V spread) ----
tx, ty, tz, tbr, _ = centers[0]
for s, nm in ((1, "TailFinR"), (-1, "TailFinL")):
    f = sphere(nm, (tx + s * 4.6, ty + 1.2, tz - 1.8), (5.6, 1.0, 2.6), FIN_M, seg=24, rings=16)
    f.rotation_euler = (math.radians(8), math.radians(-16 * s), math.radians(24 * s))
# ---- pectoral fins mid-body ----
for idx, s in ((38, 1), (44, -1)):
    x, y, z, br, t = centers[idx]
    out = (x, y); ol = math.hypot(*out) or 1
    fx, fy = x + out[0] / ol * br * 1.15 * s * 0.4 + s * 3.2, y + out[1] / ol * br * 0.6
    f = sphere(f"PecFin{idx}", (x + s * (br + 2.6), y + 1.0, z - 1.2), (4.6, 0.75, 2.0), FIN_M, seg=24, rings=16)
    f.rotation_euler = (math.radians(-12), math.radians(10 * s), math.radians(28 * s))
# ---- dorsal sail fins along the back ----
for idx in (22, 55, 80):
    x, y, z, br, t = centers[idx]
    ol = math.hypot(x, y) or 1
    dx, dy = x + x / ol * (br * 0.85), y + y / ol * (br * 0.85)
    f = sphere(f"Dorsal{idx}", (dx, dy, z + br * 0.55), (0.7, 2.6, 3.4), FIN_M, seg=20, rings=12)
    f.rotation_euler = (0, math.atan2(dy, dx), math.radians(-14))

# ---- emissive plankton dots scattered over body surface ----
for k in range(240):
    i = random.randrange(4, N - 1)
    x, y, z, br, t = centers[i]
    th = random.uniform(0, 2 * math.pi); ph = random.uniform(-0.5, 1.1)
    dx = math.cos(th) * math.cos(ph); dy = math.sin(th) * math.cos(ph); dz = math.sin(ph)
    loc = (x + dx * br * 1.0, y + dy * br * 0.94, z + dz * br * 1.03)
    r = random.uniform(0.10, 0.26)
    sphere(f"Dot{k}", loc, (r, r, r), DOT_M if k % 4 else DOT_M2, seg=8, rings=6)

root = bpy.data.objects.new("Sorakujira", None); bpy.context.collection.objects.link(root)
for o in list(bpy.context.collection.objects):
    if o != root and o.parent is None: o.parent = root

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "sorakujira.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "sorakujira.glb"), export_format="GLB")
print("SORAKUJIRA DONE")
