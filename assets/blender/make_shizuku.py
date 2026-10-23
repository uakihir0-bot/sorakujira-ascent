"""Shizuku - teardrop spirit player character for SORAKUJIRA.
Builds the character, saves shizuku.blend and exports shizuku.glb.
Origin: bottom-center of body. Total height ~1.2. Facing -Y.
"""
import bpy, math, os

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # assets/
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, roughness=0.35, metallic=0.0, emission=None, emission_strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "DITHERED"
    return m

BODY_M  = mat("ShizukuBody", (0.90, 0.95, 1.00), 0.22)
CORE_M  = mat("GlowCore", (0.35, 0.85, 1.00), 0.3, emission=(0.30, 0.80, 1.00), emission_strength=3.0)
FIN_M   = mat("RibbonFin", (0.98, 0.80, 0.88), 0.35)
FIN_M2  = mat("RibbonFinTip", (0.65, 0.85, 1.00), 0.35)
EYE_M   = mat("Eye", (0.02, 0.02, 0.04), 0.12)
HL_M    = mat("Highlight", (1, 1, 1), 0.15, emission=(1, 1, 1), emission_strength=0.6)
CHEEK_M = mat("Cheek", (1.00, 0.60, 0.68), 0.5)
CREAM_M = mat("Cream", (1.00, 0.90, 0.76), 0.5)

def finish(obj, material, smooth=True):
    if material: obj.data.materials.append(material)
    if smooth and hasattr(obj.data, "polygons"):
        for p in obj.data.polygons: p.use_smooth = True
    return obj

def sphere(name, loc, scale, material, seg=32, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    return finish(o, material)

# ---- teardrop body via lathe profile (rings around Z) ----
profile = [  # (radius, z)
    (0.001, 0.00), (0.20, 0.02), (0.34, 0.10), (0.44, 0.26), (0.475, 0.44),
    (0.45, 0.60), (0.385, 0.76), (0.29, 0.90), (0.185, 1.02), (0.09, 1.12), (0.001, 1.20),
]
verts, faces = [], []
SEG = 40
for r, z in profile:
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        verts.append((r * math.cos(a), r * math.sin(a), z))
for j in range(len(profile) - 1):
    for i in range(SEG):
        a = j * SEG + i; b = j * SEG + (i + 1) % SEG
        faces.append((a, b, b + SEG, a + SEG))
mesh = bpy.data.meshes.new("BodyMesh"); mesh.from_pydata(verts, [], faces); mesh.update()
body = bpy.data.objects.new("Body", mesh); bpy.context.collection.objects.link(body)
finish(body, BODY_M)
# slight forward plumpness
body.scale = (1.0, 1.04, 1.0)

# ---- glowing core at the belly (front = -Y) ----
sphere("GlowCore", (0, -0.425, 0.44), (0.165, 0.11, 0.20), CORE_M)
sphere("CoreHalo", (0, -0.515, 0.44), (0.07, 0.035, 0.09), HL_M)

# ---- ribbon fins: two long tapered segments sweeping up/back from the head ----
def fin(side):
    # base segment
    f1 = sphere("FinBase_" + side, (0.20 * (1 if side == "R" else -1), 0.06, 1.16),
                (0.085, 0.045, 0.30), FIN_M)
    f1.rotation_euler = (math.radians(-18), math.radians(26 * (1 if side == "R" else -1)), 0)
    # tip segment, longer and thinner, continuing the sweep
    f2 = sphere("FinTip_" + side, (0.335 * (1 if side == "R" else -1), 0.17, 1.40),
                (0.06, 0.032, 0.30), FIN_M2)
    f2.rotation_euler = (math.radians(-34), math.radians(38 * (1 if side == "R" else -1)), 0)
fin("L"); fin("R")

# ---- face ----
sphere("EyeL", (-0.175, -0.415, 0.74), (0.052, 0.030, 0.078), EYE_M)
sphere("EyeR", ( 0.175, -0.415, 0.74), (0.052, 0.030, 0.078), EYE_M)
sphere("HL_L", (-0.192, -0.442, 0.775), (0.016, 0.010, 0.024), HL_M)
sphere("HL_R", ( 0.158, -0.442, 0.775), (0.016, 0.010, 0.024), HL_M)
sphere("CheekL", (-0.295, -0.375, 0.60), (0.075, 0.040, 0.055), CHEEK_M)
sphere("CheekR", ( 0.295, -0.375, 0.60), (0.075, 0.040, 0.055), CHEEK_M)
# tiny mouth: small dark flattened torus arc substitute - a mini sphere squashed
sphere("Mouth", (0, -0.452, 0.615), (0.030, 0.014, 0.020), EYE_M)

# ---- little arms and feet ----
a = sphere("ArmL", (-0.47, -0.10, 0.46), (0.09, 0.09, 0.20), BODY_M); a.rotation_euler = (0, 0, math.radians(24))
a = sphere("ArmR", ( 0.47, -0.10, 0.52), (0.09, 0.09, 0.20), BODY_M); a.rotation_euler = (0, 0, math.radians(-30))
sphere("FootL", (-0.20, -0.16, 0.045), (0.13, 0.17, 0.05), CREAM_M)
sphere("FootR", ( 0.20, -0.16, 0.045), (0.13, 0.17, 0.05), CREAM_M)

# parent everything to an empty for clean game import
root = bpy.data.objects.new("Shizuku", None); bpy.context.collection.objects.link(root)
for o in list(bpy.context.collection.objects):
    if o != root and o.parent is None:
        o.parent = root

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "shizuku.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "shizuku.glb"), export_format="GLB")
print("SHIZUKU DONE")
