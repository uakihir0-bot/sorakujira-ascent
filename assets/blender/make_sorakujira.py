"""Sorakujira v4 - the colossal sky whale, ring-lofted body, whale proportions.

v4 fixes over v3 (mass distribution / countershading kept - they worked):
- Plankton dots rebuilt: 2048x1024 emission canvas, ~1050 small soft
  speckles concentrated in a dorsal band + one lateral stripe per side,
  sparse flanks, belly clean, calm zones at both UV poles; dots absent
  from the base skin map so daylight reads as skin, not polka dots.
- Rostrum fully rounded: ellipsoidal radius falloff over the last ~3% of
  length with dense tip stations - no point, no UV pinch star.
- Pectoral fins: broad teardrop (max chord ~3.9), span swept back ~30 deg
  with slight dorsal dihedral, chord blended toward world-horizontal so
  they read as wing-like fins, not a vertical blade.
- Tail flukes rebuilt as a grid-lofted foil: airfoil chord sections,
  root->tip thickness taper (0.36 -> 0.15), gentle span camber toward
  the belly, deeper centre notch.
- Skin mottling contrast raised toward +-8% luminance, larger blotches.
Body length (arc) ~80 units, coil height ~60, head top / tail bottom.
Saves sorakujira.blend and exports sorakujira.glb.
"""
import bpy, math, os, random
from mathutils import Vector

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(42)

# ---------------------------------------------------------------- materials
def mat(name, color, roughness=0.5, emission=None, es=0.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metal
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = es
    return m

FIN_M   = mat("WhaleFin",   (0.085, 0.165, 0.375), 0.44)
FIN_M2  = mat("WhaleFinDorsal", (0.11, 0.21, 0.46), 0.44)
EYEBALL_M = mat("Eyeball",  (0.006, 0.006, 0.015), 0.07)
IRIS_M  = mat("Iris", (0.85, 0.55, 0.14), 0.28, emission=(0.70, 0.40, 0.08), es=0.4)
PUPIL_M = mat("Pupil", (0.0, 0.0, 0.0), 0.12)
HL_M    = mat("Highlight", (1, 1, 1), 0.2, emission=(1, 1, 1), es=0.9)
MOUTH_M = mat("MouthLine", (0.015, 0.03, 0.085), 0.55)
BLOW_M  = mat("Blowhole", (0.02, 0.035, 0.09), 0.6)
SOCKET_M = mat("EyeSocket", (0.05, 0.09, 0.22), 0.5)

def finish(o, material, smooth=True):
    if material: o.data.materials.append(material)
    if smooth and hasattr(o.data, "polygons"):
        for p in o.data.polygons: p.use_smooth = True
    return o

def sphere(name, loc, scale, material, seg=24, rings=18):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    return finish(o, material)

def lerp3(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

# ------------------------------------------------------------------- path
HEIGHT = 60.0
def path(t):
    ang = t * math.radians(300)
    r = 13.0 * (1.0 - 0.45 * t)
    return Vector((r * math.cos(ang), r * math.sin(ang), 4.0 + t * HEIGHT))

def frame(t):
    """centre, tangent, e1 (radial-out, perp to tangent), e2 (= T x e1)."""
    c = path(t)
    e = 0.0015
    tan = (path(min(1.0, t + e)) - path(max(0.0, t - e)))
    tan.normalize()
    ang = t * math.radians(300)
    radial = Vector((math.cos(ang), math.sin(ang), 0))
    e1 = radial - tan * radial.dot(tan)
    e1.normalize()
    e2 = tan.cross(e1); e2.normalize()
    return c, tan, e1, e2

# radius profile v3: (t, r) - great-whale mass distribution, head <= girth
RKEYS = [(0.00, 0.30), (0.04, 0.55), (0.10, 1.05), (0.20, 2.05), (0.32, 3.15),
         (0.45, 4.15), (0.56, 4.80), (0.66, 5.05), (0.75, 5.02), (0.82, 4.95),
         (0.88, 4.80), (0.92, 4.58), (0.96, 4.22), (0.985, 3.78), (1.00, 3.02)]
def radius(t):
    if t <= RKEYS[0][0]: return RKEYS[0][1]
    for (t0, r0), (t1, r1) in zip(RKEYS, RKEYS[1:]):
        if t <= t1:
            s = (t - t0) / (t1 - t0)
            return r0 + (r1 - r0) * (s * s * (3 - 2 * s))
    return RKEYS[-1][1]

def ring_scale(t_len):
    """(sx along e1, sz along e2): head slightly wider than tall, t>0.86."""
    hf = smooth(0.86, 0.97, t_len)
    return 1.0 + 0.12 * hf, 1.0 - 0.09 * hf

# ------------------------------------------------------------------- loft
NST, MSEG = 150, 24
stations = []  # (centre, tan, e1, e2, R, v)
c0, tan0, e10, e20 = frame(0.0)
stations.append((c0 - tan0 * 0.9, tan0, e10, e20, 0.05, 0.0))
for i in range(NST):
    t = i / (NST - 1)
    c, tan, e1, e2 = frame(t)
    stations.append((c, tan, e1, e2, radius(t), 0.02 + 0.96 * t))
c1, tan1, e11, e21 = frame(1.0)
# v4: fully rounded rostrum - ellipsoidal falloff over the last ~3% of
# length (axial radius 2.7 from R0), dense stations near the tip so the
# profile never comes to a point and UVs cannot pinch into a star.
R0, AX = radius(1.0), 2.7
for s in (0.14, 0.30, 0.46, 0.60, 0.72, 0.82, 0.89, 0.94, 0.975, 0.995, 1.0):
    rr = max(R0 * math.sqrt(max(1.0 - s * s, 0.0)), 0.05)
    stations.append((c1 + tan1 * (AX * s), tan1, e11, e21, rr,
                     0.98 + 0.02 * s ** 0.7))

DARK_TAIL = (0.082, 0.150, 0.315)   # deep indigo (toward #16294f)
DARK_HEAD = (0.100, 0.180, 0.360)
PALE = (0.810, 0.845, 0.900)        # pale warm-blue belly

verts, cols, uvs, faces = [], [], [], []
for (c, tan, e1, e2, R, v) in stations:
    t_len = min(1.0, max(0.0, v))
    dark = lerp3(DARK_TAIL, DARK_HEAD, t_len)
    sx, sz = ring_scale(t_len)
    for j in range(MSEG + 1):
        th = 2 * math.pi * (j % MSEG) / MSEG
        co, si = math.cos(th), math.sin(th)
        off = e1 * (co * R * sx) + e2 * (si * R * sz)
        verts.append(tuple(c + off))
        belly = smooth(0.55, -0.9, co)      # 1 on the inward (belly) side
        col = lerp3(PALE, dark, 1.0 - belly)
        # eye-socket shading: dark patch around each eye (t 0.88-0.99, +-e2)
        if 0.87 < t_len < 0.995:
            for s in (1, -1):
                d = co * (-0.10) + si * (0.995 * s)
                if d > 0.80:
                    f = smooth(0.80, 0.985, d) * smooth(0.995, 0.90, t_len)
                    col = tuple(x * (1.0 - 0.48 * f) for x in col)
        cols.append((*col, 1.0))
        uvs.append((j / MSEG, v))
W = MSEG + 1
for i in range(len(stations) - 1):
    for j in range(MSEG):
        a = i * W + j; b = a + 1; d = a + W
        faces.append((a, b, d + 1, d))
mesh = bpy.data.meshes.new("WhaleBodyMesh")
mesh.from_pydata(verts, [], faces); mesh.update()
uv_layer = mesh.uv_layers.new(name="UVMap")
for poly in mesh.polygons:
    for li in poly.loop_indices:
        uv_layer.data[li].uv = uvs[mesh.loops[li].vertex_index]
col_attr = mesh.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
for i, c in enumerate(cols): col_attr.data[i].color = c
mesh.color_attributes.active = col_attr
body = bpy.data.objects.new("WhaleBody", mesh)
bpy.context.collection.objects.link(body)
for p in mesh.polygons: p.use_smooth = True

# ------------------------------------------------- canvas skin textures
TW, TH = 2048, 1024
def splat(px, cx, cy, r, col, strength, wrap=True):
    r = int(r)
    xs_wrap = wrap and (cx - r < 0 or cx + r >= TW)
    for dy in range(-r, r + 1):
        rem = 1.0 - (dy / r) ** 2
        if rem < 0.0: continue
        dxm = int(r * math.sqrt(rem))
        y = int(cy + dy)
        if not (0 <= y < TH): continue
        for dx in range(-dxm, dxm + 1):
            d2 = (dx * dx + dy * dy) / float(r * r)
            if d2 > 1.0: continue
            f = (1.0 - d2) ** 1.5 * strength
            xs = [int(cx + dx)]
            if xs_wrap: xs += [int(cx + dx) + TW, int(cx + dx) - TW]
            for x in xs:
                if 0 <= x < TW:
                    idx = (y * TW + x) * 4
                    for ch in range(3):
                        px[idx + ch] += (col[ch] - px[idx + ch]) * min(1.0, f)

# base colour: bright neutral (multiplies the vertex colours), mottled skin
base_px = [0.0] * (TW * TH * 4)
for k in range(0, len(base_px), 4):
    base_px[k:k + 4] = (0.88, 0.90, 0.96, 1.0)
for _ in range(240):   # lighter slate blotches (real whale skin mottling)
    splat(base_px, random.uniform(0, TW), random.uniform(0, TH),
          random.uniform(60, 230), (0.99, 1.01, 1.05), random.uniform(0.10, 0.22))
for _ in range(160):   # darker slate blotches
    splat(base_px, random.uniform(0, TW), random.uniform(0, TH),
          random.uniform(44, 180), (0.56, 0.65, 0.80), random.uniform(0.10, 0.22))
for _ in range(420):   # fine grain speckle
    splat(base_px, random.uniform(0, TW), random.uniform(0, TH),
          random.uniform(5, 16), (0.70, 0.76, 0.88), random.uniform(0.04, 0.09))
# faint lengthwise ventral pleats: lower half of u (belly u~0.5), throat v>0.80
for pu in range(24):
    u = 0.315 + pu * (0.37 / 23.0)
    x = u * TW
    amp = 0.16 * math.sin(math.pi * (pu / 23.0)) ** 0.5
    for y in range(int(0.80 * TH), TH):
        vv = (y / TH - 0.80) / 0.20
        a = amp * math.sin(math.pi * min(1.0, vv * 1.06))
        for dx in (-1, 0, 1):
            wgt = (0.5, 1.0, 0.5)[dx + 1] * a
            xx = int(x) + dx
            if 0 <= xx < TW:
                idx = (y * TW + xx) * 4
                for ch in range(3):
                    base_px[idx + ch] *= (1.0 - wgt * 0.55)
base_img = bpy.data.images.new("SkinTex", TW, TH, alpha=False)
base_img.pixels = base_px
base_img.pack()   # NOTE: pack BEFORE touching colorspace (setting it first un-packs)
base_img.colorspace_settings.name = 'sRGB'

# plankton emission dots v4: small soft speckles on the 2048x1024 canvas,
# concentrated in a dorsal band (u near 0/1) + one lateral stripe per side
# (u 0.25 / 0.75), sparse mid-flank, belly (u 0.40-0.60) essentially clean,
# calm zones near both UV poles so nothing streaks at the caps. Dots live
# ONLY in this emission map - the base skin map carries none of them.
emis_px = [0.0] * (TW * TH * 4)
for k in range(0, len(emis_px), 4): emis_px[k + 3] = 1.0
def draw_dot(cx, cy, rv, col, peak):
    rx = rv * 5.0   # pre-compensate UV anisotropy so dots read round
    rxi, ryi = int(rx) + 1, int(rv) + 1
    for dy in range(-ryi, ryi + 1):
        y = int(cy + dy)
        if not (0 <= y < TH): continue
        for dx in range(-rxi, rxi + 1):
            d2 = (dx / rx) ** 2 + (dy / rv) ** 2
            if d2 > 1.0: continue
            f = (1.0 - d2) ** 2 * peak
            for xx in (int(cx + dx), int(cx + dx) + TW, int(cx + dx) - TW):
                if 0 <= xx < TW:
                    idx = (y * TW + xx) * 4
                    for ch in range(3):
                        emis_px[idx + ch] = max(emis_px[idx + ch], col[ch] * f)
def dot_u(kind):
    if kind == 0:    # dorsal band (wraps at u 0/1)
        return random.gauss(0.0, 0.085) % 1.0
    if kind == 1:    # one lateral stripe per side
        return (0.25 if random.random() < 0.5 else 0.75) + random.gauss(0.0, 0.040)
    while True:      # sparse flank - belly zone stays clean
        u = random.random()
        if not (0.40 < u < 0.60): return u
for _ in range(1050):
    r01 = random.random()
    kind = 0 if r01 < 0.46 else (1 if r01 < 0.76 else 2)
    u = dot_u(kind) % 1.0
    v = random.random()
    if v < 0.014 or v > 0.980:   # pole calm zones
        v = 0.014 + 0.966 * random.random()
    rv = 1.0 + 1.8 * random.random() ** 2.2
    if random.random() < 0.05:   # rare brighter dorsal accent
        u = random.gauss(0.0, 0.07) % 1.0
        rv = random.uniform(2.2, 3.0)
    col = (0.62, 0.92, 1.00) if random.random() < 0.80 else (1.00, 0.78, 0.38)
    draw_dot(u * TW, v * TH, rv, col, random.uniform(0.30, 0.95))
emis_img = bpy.data.images.new("PlanktonTex", TW, TH, alpha=False)
emis_img.pixels = emis_px
emis_img.pack()   # pack BEFORE colorspace (setting it first un-packs)
emis_img.colorspace_settings.name = 'sRGB'

# roughness canvas: glossy back (u~0) 0.36 -> matte belly (u~0.5) 0.52
RW, RH = 256, 64
rgh_px = [0.0] * (RW * RH * 4)
for x in range(RW):
    u = x / RW
    bellyness = 0.5 + 0.5 * math.cos(2 * math.pi * (u - 0.5))
    rv = 0.44 + 0.14 * bellyness
    for y in range(RH):
        idx = (y * RW + x) * 4
        rgh_px[idx:idx + 4] = (rv, rv, rv, 1.0)
rgh_img = bpy.data.images.new("RoughTex", RW, RH, alpha=False)
rgh_img.pixels = rgh_px
rgh_img.pack()   # pack BEFORE colorspace (see note above)
rgh_img.colorspace_settings.name = 'Non-Color'

skin = bpy.data.materials.new("WhaleSkin"); skin.use_nodes = True
nt = skin.node_tree; nt.nodes.clear()
out_n = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
texb = nt.nodes.new("ShaderNodeTexImage"); texb.image = base_img
mixn = nt.nodes.new("ShaderNodeMixRGB"); mixn.blend_type = 'MULTIPLY'
mixn.inputs[0].default_value = 1.0
nt.links.new(vc.outputs["Color"], mixn.inputs[1])
nt.links.new(texb.outputs["Color"], mixn.inputs[2])
nt.links.new(mixn.outputs["Color"], bsdf.inputs["Base Color"])
texr = nt.nodes.new("ShaderNodeTexImage"); texr.image = rgh_img
nt.links.new(texr.outputs["Color"], bsdf.inputs["Roughness"])
texe = nt.nodes.new("ShaderNodeTexImage"); texe.image = emis_img
nt.links.new(texe.outputs["Color"], bsdf.inputs["Emission Color"])
bsdf.inputs["Emission Strength"].default_value = 1.0
nt.links.new(bsdf.outputs[0], out_n.inputs["Surface"])
mesh.materials.append(skin)
sub = body.modifiers.new("Subsurf", "SUBSURF"); sub.levels = 1; sub.render_levels = 1

# ------------------------------------------------------- fins from outlines
def world_outline(name, origin, ax_a, ax_b, pts2d, thick, material, bend=None):
    vs = []
    for a, b in pts2d:
        p = origin + ax_a * a + ax_b * b
        if bend: p = p + bend(a, b)
        vs.append(tuple(p))
    m = bpy.data.meshes.new(name + "Mesh"); m.from_pydata(vs, [], [tuple(range(len(vs)))])
    m.update()
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    mod = o.modifiers.new("Solid", "SOLIDIFY"); mod.thickness = thick; mod.offset = 0.0
    bev = o.modifiers.new("Bevel", "BEVEL"); bev.width = 0.055; bev.segments = 2
    bev.limit_method = 'ANGLE'
    return finish(o, material)

# tail flukes v4: grid-lofted foil, span +-8.8 (~0.22 x body length).
# Airfoil chord sections, root->tip thickness taper (0.36 -> 0.15), gentle
# span camber (tips arc toward the belly), deeper centre notch.
tc, ttan, te1, te2 = frame(0.0)
fspan = Vector((0, 0, 1)).cross(ttan); fspan.normalize()
fchord = ttan - fspan * ttan.dot(fspan); fchord.normalize()
fn = fchord.cross(fspan); fn.normalize()
if fn.dot(te1) < 0: fn = -fn          # fn = dorsal side
froot = tc - ttan * 0.4
LEAD_K  = [(0.0, 1.20), (3.0, 0.90), (5.8, 0.20), (7.8, -0.90), (8.8, -2.55)]
TRAIL_K = [(0.0, -0.05), (1.2, -0.92), (3.6, -1.28), (6.2, -1.72), (8.8, -2.65)]
def prof1(keys, x):
    if x <= keys[0][0]: return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            s = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * (s * s * (3 - 2 * s))
    return keys[-1][1]
NSF, NAF = 37, 8
fverts, ffaces = [], []
for side in (1, -1):   # dorsal surface grid, then ventral surface grid
    for i in range(NSF):
        b = -8.8 + 17.6 * (i / (NSF - 1))
        ab = abs(b)
        al, at = prof1(LEAD_K, ab), prof1(TRAIL_K, ab)
        tmax = 0.36 + (0.15 - 0.36) * (ab / 8.8)
        cam = -0.55 * (ab / 8.8) ** 2
        for j in range(NAF):
            s = j / (NAF - 1)
            a = al + (at - al) * s
            th = tmax * (0.30 + 0.70 * math.sin(math.pi * s)) * 0.5
            p = froot + fchord * a + fspan * b + fn * (cam + side * th)
            fverts.append(tuple(p))
for i in range(NSF - 1):
    for j in range(NAF - 1):
        a0 = i * NAF + j; b0 = a0 + NAF
        ffaces.append((a0, b0, b0 + 1, a0 + 1))                 # dorsal
        c0 = NSF * NAF + a0; d0 = NSF * NAF + b0
        ffaces.append((c0, c0 + 1, d0 + 1, d0))                 # ventral
for i in range(NSF - 1):                                        # edge walls
    t0, t1 = i * NAF, (i + 1) * NAF
    b0, b1 = NSF * NAF + t0, NSF * NAF + t1
    ffaces.append((t0, b0, b1, t1))                             # leading
    t0, t1 = i * NAF + NAF - 1, (i + 1) * NAF + NAF - 1
    b0, b1 = NSF * NAF + t0, NSF * NAF + t1
    ffaces.append((t0, t1, b1, b0))                             # trailing
for j in range(NAF - 1):                                        # tip walls
    t0 = (NSF - 1) * NAF + j; b0 = NSF * NAF + t0
    ffaces.append((t0, b0, b0 + 1, t0 + 1))                     # +span tip
    ffaces.append((j, j + 1, NSF * NAF + j + 1, NSF * NAF + j))  # -span tip
fm = bpy.data.meshes.new("TailFlukesMesh"); fm.from_pydata(fverts, [], ffaces)
fm.update()
flukes = bpy.data.objects.new("TailFlukes", fm)
bpy.context.collection.objects.link(flukes)
finish(flukes, FIN_M)

# pectoral fins: ~9.6 long (0.12 x L), broad teardrop, at t=0.78 lower sides,
# angled out / down / back so they clear the body silhouette
for s, nm in ((1, "PecFinR"), (-1, "PecFinL")):
    c, tan, e1, e2 = frame(0.78)
    R = radius(0.78)
    base = c + e2 * (s * R * 0.70) + e1 * (-R * 0.34)
    # v4 wing-like fins: span swept back ~30 deg with slight dorsal
    # dihedral; chord blended toward world-horizontal; broad teardrop
    # outline (max chord ~3.9 at ~1/3 span) - no more vertical blade.
    span = e2 * s * math.cos(math.radians(30)) \
        - tan * math.sin(math.radians(30)) + e1 * 0.16
    span.normalize()
    chord_t = tan - span * tan.dot(span); chord_t.normalize()
    chord_h = Vector((0, 0, 1)).cross(span)
    if chord_h.length < 1e-4: chord_h = chord_t.copy()
    chord_h.normalize()
    if chord_h.dot(chord_t) < 0: chord_h = -chord_h
    chord = chord_h * 0.62 + chord_t * 0.38
    chord = chord - span * chord.dot(span); chord.normalize()
    PEC = [(0.0, 1.35), (1.2, 1.95), (2.8, 2.15), (4.6, 1.95), (6.6, 1.45),
           (8.4, 0.75), (9.6, -0.05), (8.6, -0.80), (6.4, -1.45),
           (4.0, -1.80), (1.8, -1.75), (0.0, -1.20)]
    world_outline(nm, base, span, chord, PEC, 0.24, FIN_M,
                  bend=lambda a, b: Vector((0, 0, -0.018 * a)))

# dorsal fin at t=0.30 (clearly visible in profile) on the outer/back side
c, tan, e1, e2 = frame(0.30)
R = radius(0.30)
DOR = [(0.0, 0.0), (0.80, 1.40), (1.60, 2.20), (2.30, 1.70), (3.40, 0.0)]
world_outline("DorsalMain", c + e1 * (R * 0.90), -tan, e1, DOR, 0.16, FIN_M2)
# smaller trailing dorsal bump at t=0.14
c, tan, e1, e2 = frame(0.14)
R = radius(0.14)
DOR2 = [(0.0, 0.0), (0.45, 0.70), (0.95, 0.95), (1.35, 0.60), (1.90, 0.0)]
world_outline("DorsalRear", c + e1 * (R * 0.90), -tan, e1, DOR2, 0.12, FIN_M2)
# dorsal ridge: low lofted crest along the back, t=0.08..0.30
rverts, rfaces = [], []
RST = 12
for i in range(RST):
    tt = 0.08 + (0.30 - 0.08) * (i / (RST - 1))
    c, tan, e1, e2 = frame(tt)
    R = radius(tt)
    h = 0.55 * math.sin(math.pi * (i / (RST - 1))) ** 0.8 + 0.06
    rverts.append(tuple(c + e1 * (R * 0.99)))
    rverts.append(tuple(c + e1 * (R * 0.99 + h)))
for i in range(RST - 1):
    a = i * 2
    rfaces.append((a, a + 1, a + 3, a + 2))
rm = bpy.data.meshes.new("DorsalRidgeMesh"); rm.from_pydata(rverts, [], rfaces); rm.update()
ridge = bpy.data.objects.new("DorsalRidge", rm); bpy.context.collection.objects.link(ridge)
rmod = ridge.modifiers.new("Solid", "SOLIDIFY"); rmod.thickness = 0.07; rmod.offset = 0.0
finish(ridge, FIN_M2)

# ---------------------------------------------------------------- head bits
# eyes: ~2.2x v2, lower + forward on the head, socket rim + dark VC patch
ec, etan, ee1, ee2 = frame(0.925)
ER = radius(0.925)
esz = ring_scale(0.925)[1]
for s, nm in ((1, "R"), (-1, "L")):
    off = ee2 * (s * ER * esz * 0.80) + ee1 * (-ER * 0.06) + etan * (ER * 0.24)
    ep = ec + off
    out_dir = (ee2 * s * 0.92 + ee1 * (-0.06) + etan * 0.38); out_dir.normalize()
    q = out_dir.to_track_quat('Z', 'Y')
    rim = sphere(f"EyeSocket{nm}", tuple(ep - out_dir * 0.34), (1.16, 1.16, 0.38), SOCKET_M, seg=24, rings=16)
    rim.rotation_mode = 'QUATERNION'; rim.rotation_quaternion = q
    sphere(f"Eyeball{nm}", tuple(ep), (1.02,) * 3, EYEBALL_M, seg=28, rings=20)
    iris = sphere(f"Iris{nm}", tuple(ep + out_dir * 0.88), (0.52, 0.52, 0.16), IRIS_M, seg=24, rings=16)
    iris.rotation_mode = 'QUATERNION'; iris.rotation_quaternion = q
    pup = sphere(f"Pupil{nm}", tuple(ep + out_dir * 1.00), (0.27, 0.27, 0.12), PUPIL_M, seg=20, rings=14)
    pup.rotation_mode = 'QUATERNION'; pup.rotation_quaternion = q
    sphere(f"EyeHL{nm}", tuple(ep + out_dir * 1.00 + Vector((0, 0, 0.20))),
           (0.10,) * 3, HL_M, seg=12, rings=10)
    # mouth line: on the surface from the snout back ~0.10 x L, sweeping
    # down toward the belly as it runs below/behind the eye
    pts = []
    for k in range(31):
        f = k / 30
        tt = 0.997 - 0.102 * f
        c, tan, e1, e2 = frame(tt)
        R = radius(tt)
        sx, sz = ring_scale(tt)
        pts.append(tuple(c + e2 * (s * R * sz * 0.985)
                         + e1 * (-R * sx * (0.05 + 0.30 * f) * 0.99)))
    cu = bpy.data.curves.new(f"Mouth{nm}", 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = 0.06; cu.bevel_resolution = 2
    spl = cu.splines.new('POLY'); spl.points.add(len(pts) - 1)
    for p, co in zip(spl.points, pts): p.co = (*co, 1.0)
    mo = bpy.data.objects.new(f"Mouth{nm}", cu); bpy.context.collection.objects.link(mo)
    mo.data.materials.append(MOUTH_M)
    bpy.context.view_layer.objects.active = mo; mo.select_set(True)
    bpy.ops.object.convert(target='MESH'); mo.select_set(False)
# blowhole: double-comma dark inset on top of the head (t=0.96)
bc, btan, be1, be2 = frame(0.96)
BR = radius(0.96)
bsx = ring_scale(0.96)[0]
for s in (1, -1):
    bp = bc + be1 * (BR * bsx * 0.90) + be2 * (s * 0.55) + btan * (BR * 0.06)
    o = sphere("Blowhole", tuple(bp), (0.30, 0.58, 0.10), BLOW_M, seg=18, rings=12)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = be1.to_track_quat('Z', 'Y')
    o.rotation_quaternion = o.rotation_quaternion @ \
        __import__('mathutils').Quaternion((0, 0, 1), math.radians(18 * s))

# ------------------------------------------------------------------ wrap up
root = bpy.data.objects.new("Sorakujira", None); bpy.context.collection.objects.link(root)
for o in list(bpy.context.collection.objects):
    if o != root and o.parent is None: o.parent = root

dg = bpy.context.evaluated_depsgraph_get()
tot = sum(len(o.evaluated_get(dg).data.polygons) for o in bpy.context.collection.objects
          if o.type == 'MESH')
print("EVALUATED POLYGONS:", tot)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "sorakujira.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "sorakujira.glb"),
                          export_format="GLB", export_apply=True)
print("SORAKUJIRA V4 DONE")
