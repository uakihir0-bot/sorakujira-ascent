"""Star-crystal prop cluster for SORAKUJIRA. Saves crystal.blend / crystal.glb."""
import bpy, math, os

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, roughness=0.18, emission=None, es=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = 0.1
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = es
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "DITHERED"
    return m

VIOLET = mat("CrystalViolet", (0.55, 0.40, 0.95), emission=(0.45, 0.30, 1.0), es=0.55, alpha=0.92)
CYAN   = mat("CrystalCyan", (0.40, 0.85, 1.00), emission=(0.30, 0.75, 1.0), es=0.55, alpha=0.92)
ROCK   = mat("StarRock", (0.16, 0.15, 0.26), roughness=0.85)

def crystal(name, loc, height, radius, material, tilt=(0, 0, 0)):
    # tapered 6-sided spike: cone with a wide base ring (two cones = octahedron-ish shard)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=radius, radius2=radius * 0.34,
                                    depth=height * 0.72, location=(loc[0], loc[1], loc[2] + height * 0.36))
    top = bpy.context.object; top.name = name
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=radius * 0.34, radius2=0.0,
                                    depth=height * 0.28, location=(loc[0], loc[1], loc[2] + height * 0.86))
    tip = bpy.context.object; tip.name = name + "Tip"
    for o in (top, tip):
        o.data.materials.append(material)
        o.rotation_euler = tilt
    return top

crystal("ShardA", (0.0, 0.0, 0.0), 1.90, 0.34, VIOLET, (math.radians(4), math.radians(-3), 0))
crystal("ShardB", (0.42, 0.14, 0.0), 1.30, 0.26, CYAN, (math.radians(-10), math.radians(12), 0))
crystal("ShardC", (-0.40, 0.20, 0.0), 1.10, 0.22, CYAN, (math.radians(8), math.radians(-14), 0))
crystal("ShardD", (-0.16, -0.36, 0.0), 0.80, 0.18, VIOLET, (math.radians(-14), math.radians(-6), 0))
crystal("ShardE", (0.30, -0.30, 0.0), 0.62, 0.15, VIOLET, (math.radians(12), math.radians(10), 0))

# rocky base
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.62, location=(0, 0, 0.02))
base = bpy.context.object; base.name = "BaseRock"; base.scale = (1.15, 1.15, 0.42)
base.data.materials.append(ROCK)

root = bpy.data.objects.new("StarCrystal", None); bpy.context.collection.objects.link(root)
for o in list(bpy.context.collection.objects):
    if o != root and o.parent is None: o.parent = root

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "crystal.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "crystal.glb"), export_format="GLB")
print("CRYSTAL DONE")
