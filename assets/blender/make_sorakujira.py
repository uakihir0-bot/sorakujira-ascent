"""Sorakujira v5 - craft overhaul: procedural baked skin + carved head.

What changed vs v4 (silhouette / proportions / countershading kept -
they were sound; the SURFACE and DETAIL method is new):
- SKIN: built as a layered procedural shader-node material (large
  mottling + mid blotches + fine grain on the albedo, longitudinal
  throat/flank creases + micro-grain as bump, roughness layered by
  belly/back + mottle, plankton as Voronoi-cell bioluminescence
  clustered on dorsal/lateral lines - no painted canvas anywhere),
  then BAKED at 4096x2048 (base colour / roughness / normal / emission)
  and the baked maps drive the final material (SSS + clearcoat on top).
- HEAD CARVED, not an egg: smooth-falloff vertex sculpt on the loft -
  melon swell, rostrum step, eye-socket depression with brow ridge,
  mouth crease, jaw narrowing below the mouth line; plus a caudal
  keel (dorsal + ventral ridges) over the rear third.
- PECTORAL FINS rebuilt as lofted airfoil sections (root thick, tip
  thin, cambered), same construction family as the tail flukes.
- EYES rebuilt: eyeball + iris disc with a radial-streak canvas
  texture + pupil + a TRANSPARENT CORNEA dome (transmission) for a
  wet, living eye.
Body length (arc) ~80 units, coil height ~60, head top / tail bottom.
Saves sorakujira.blend and exports sorakujira.glb.
"""
import bpy, math, os, random
from mathutils import Vector

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(42)

# ---------------------------------------------------------------- materials
def set_in(bsdf, name, val):
    if name in bsdf.inputs:
        bsdf.inputs[name].default_value = val

def mat(name, color, roughness=0.5, emission=None, es=0.0, metal=0.0,
        sss=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metal
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = es
    if sss > 0.0:
        set_in(b, "Subsurface Weight", sss)
        set_in(b, "Subsurface Radius", (0.55, 0.75, 1.05))
        set_in(b, "Subsurface Scale", 0.5)
    if coat > 0.0:
        set_in(b, "Coat Weight", coat)
        set_in(b, "Coat Roughness", 0.35)
    return m

FIN_M   = mat("WhaleFin",   (0.085, 0.165, 0.375), 0.44, sss=0.15, coat=0.12)
FIN_M2  = mat("WhaleFinDorsal", (0.11, 0.21, 0.46), 0.44, sss=0.15, coat=0.12)
EYEBALL_M = mat("Eyeball",  (0.006, 0.006, 0.015), 0.06)
PUPIL_M = mat("Pupil", (0.0, 0.0, 0.0), 0.12)
MOUTH_M = mat("MouthLine", (0.015, 0.03, 0.085), 0.55)
BLOW_M  = mat("Blowhole", (0.02, 0.035, 0.09), 0.6)
SOCKET_M = mat("EyeSocket", (0.016, 0.028, 0.075), 0.75)

def cornea_mat():
    m = bpy.data.materials.new("Cornea"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    b.inputs["Roughness"].default_value = 0.03
    set_in(b, "Transmission Weight", 1.0)
    set_in(b, "IOR", 1.38)
    set_in(b, "Thickness", 0.03)
    return m
CORNEA_M = cornea_mat()

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
def wrap_pi(a):
    while a > math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a

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

# ------------------------------------------------------- head sculpt (v5)
EYE_T = 0.925
_esx, _esz = ring_scale(EYE_T)
EYE_THETA = {s: math.atan2(s * 0.80 * _esz, -0.06 * _esx) for s in (1, -1)}

def mouth_theta(t, s):
    """Radial angle (ring coords) of the mouth line at length t, side s."""
    f = min(1.0, max(0.0, (0.997 - t) / 0.102))
    sx, sz = ring_scale(t)
    return math.atan2(s * 0.985 * sz, -(0.05 + 0.30 * f) * 0.99 * sx)

def sculpt_delta(t, th, co, si, R):
    """Radial offset (world units, +outward) carving the loft surface."""
    d = 0.0
    if t > 0.80:
        # eye socket depression (nearest eye centre on the ring)
        # v5.1: falloff widened slightly (0.030->0.034, 0.30->0.34) so
        # the deeper-sunk v5.1 eye assembly blends into the skin
        dth_e = min(abs(wrap_pi(th - EYE_THETA[s])) for s in (1, -1))
        g = math.exp(-((t - EYE_T) / 0.034) ** 2 - (dth_e / 0.34) ** 2)
        d -= 0.21 * g
        # brow ridge: just dorsal + slightly forward of the socket
        dth_b = min(abs(wrap_pi(th - (EYE_THETA[s] - (0.22 if EYE_THETA[s] > 0 else -0.22))))
                    for s in (1, -1))
        g2 = math.exp(-((t - 0.950) / 0.022) ** 2 - (dth_b / 0.27) ** 2)
        d += 0.075 * g2
        # melon / forehead swell over the dorsal top
        d += 0.17 * math.exp(-((t - 0.945) / 0.040) ** 2) * max(0.0, co) ** 2
        # rostrum step: shallow dip between melon and snout
        d -= 0.085 * math.exp(-((t - 0.978) / 0.011) ** 2) * max(0.0, co) ** 1.5
        if t > 0.86:
            tfade = smooth(0.88, 0.93, t) * smooth(1.0, 0.99, t)
            side = 1 if si >= 0 else -1
            thm = mouth_theta(t, side)
            # soft crease along the mouth line
            gc = math.exp(-(wrap_pi(th - thm) / 0.075) ** 2)
            d -= 0.05 * gc * tfade
            # jaw: lower head narrows below the mouth line
            over = (th - thm) if side > 0 else (thm - th)
            jw = smooth(0.02, 0.55, over) * tfade
            d -= 0.05 * R * jw
    # caudal keel: dorsal + ventral ridges over the rear third
    kf = math.exp(-((t - 0.16) / 0.13) ** 2)
    if kf > 0.003:
        d += 0.15 * kf * math.exp(-(th / 0.17) ** 2)
        d += 0.11 * kf * math.exp(-(((math.pi - abs(th)) / 0.20) ** 2))
    return d

# ------------------------------------------------------------------- loft
# v5: station sampling warped (t = 1-(1-s)^1.3) for a denser head section
NST, MSEG = 150, 32
stations = []  # (centre, tan, e1, e2, R, v)
c0, tan0, e10, e20 = frame(0.0)
stations.append((c0 - tan0 * 0.9, tan0, e10, e20, 0.05, 0.0))
for i in range(NST):
    s = i / (NST - 1)
    t = 1.0 - (1.0 - s) ** 1.30
    c, tan, e1, e2 = frame(t)
    stations.append((c, tan, e1, e2, radius(t), 0.02 + 0.96 * t))
c1, tan1, e11, e21 = frame(1.0)
# fully rounded rostrum: ellipsoidal falloff, dense tip stations (as v4)
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
        dl = sculpt_delta(t_len, th, co, si, R)
        if dl != 0.0 and off.length > 1e-6:
            off = off + off.normalized() * dl
        verts.append(tuple(c + off))
        belly = smooth(0.55, -0.9, co)      # 1 on the inward (belly) side
        col = lerp3(PALE, dark, 1.0 - belly)
        # eye-socket shading: dark patch around each eye (t 0.88-0.99, +-e2)
        if 0.87 < t_len < 0.995:
            for s in (1, -1):
                dd = co * (-0.10) + si * (0.995 * s)
                if dd > 0.80:
                    f = smooth(0.80, 0.985, dd) * smooth(0.995, 0.90, t_len)
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
sub = body.modifiers.new("Subsurf", "SUBSURF"); sub.levels = 1; sub.render_levels = 1

# ============================ procedural skin (v5) =======================
# Layered shader-node skin, baked at 4096x2048. UV convention of the
# loft: u wraps the ring (u=0/+1 dorsal centreline, 0.25/0.75 lateral,
# 0.5 belly), v runs tail(0) -> head(1). Object coords drive the 3D
# noise layers (seamless, no UV stretch); UV drives the anatomical
# masks (belly band, throat, dorsal/lateral plankton lines).
def nd(nt, typ, x=0, y=0):
    n = nt.nodes.new(typ); n.location = (x, y); return n

def lk(nt, a, ao, b, bi):
    # `a` may be a node (use its named output) or a bare socket
    src = a.outputs[ao] if hasattr(a, "outputs") else a
    nt.links.new(src, b.inputs[bi])

def mathn(nt, op, x, y, v0=None, v1=None, v2=None):
    n = nd(nt, "ShaderNodeMath", x, y); n.operation = op
    if v0 is not None: n.inputs[0].default_value = v0
    if v1 is not None: n.inputs[1].default_value = v1
    if v2 is not None: n.inputs[2].default_value = v2
    return n

def rampn(nt, stops, x, y):
    n = nd(nt, "ShaderNodeValToRGB", x, y)
    cr = n.color_ramp
    cr.elements[0].position = stops[0][0]
    cr.elements[0].color = (*stops[0][1], 1.0)
    for pos, col in stops[1:]:
        e = cr.elements.new(pos); e.color = (*col, 1.0)
    return n

def build_skin_proc():
    m = bpy.data.materials.new("WhaleSkinProc"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out_n = nd(nt, "ShaderNodeOutputMaterial", 1500, 0)
    bsdf = nd(nt, "ShaderNodeBsdfPrincipled", 1250, 0)
    lk(nt, bsdf, "BSDF", out_n, "Surface")
    uvm = nd(nt, "ShaderNodeUVMap", -1600, 300); uvm.uv_map = "UVMap"
    sep = nd(nt, "ShaderNodeSeparateXYZ", -1450, 300)
    lk(nt, uvm, "UV", sep, "Vector")
    tc = nd(nt, "ShaderNodeTexCoord", -1600, -100)
    vc = nd(nt, "ShaderNodeVertexColor", -1600, 600); vc.layer_name = "Col"
    U, V, OBJ = sep.outputs["X"], sep.outputs["Y"], tc.outputs["Object"]

    def noise(x, y, scale, detail=2.0, rough=0.7):
        n = nd(nt, "ShaderNodeTexNoise", x, y)
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        nt.links.new(OBJ, n.inputs["Vector"])
        return n
    def voro(x, y, scale):
        n = nd(nt, "ShaderNodeTexVoronoi", x, y)
        n.inputs["Scale"].default_value = scale
        n.inputs["Randomness"].default_value = 1.0
        nt.links.new(OBJ, n.inputs["Vector"])
        return n

    # ---- albedo modulation (near-neutral; vertex colours carry hue) --
    nL = noise(-1250, 500, 0.045, 3.0)
    rL = rampn(nt, [(0.0, (0.80, 0.85, 1.02)), (0.5, (0.97, 0.99, 1.02)),
                    (1.0, (1.14, 1.11, 1.00))], -1050, 500)
    lk(nt, nL, "Fac", rL, "Fac")
    vM = voro(-1250, 200, 0.09)
    rV = rampn(nt, [(0.0, (1.05, 1.00, 0.94)), (0.55, (0.99, 1.00, 1.02)),
                    (1.0, (0.93, 0.98, 1.09))], -1050, 200)
    lk(nt, vM, "Distance", rV, "Fac")
    nM = noise(-1250, -50, 0.35, 2.0)
    rM = rampn(nt, [(0.0, (0.89, 0.92, 1.02)), (1.0, (1.09, 1.07, 0.99))], -1050, -50)
    lk(nt, nM, "Fac", rM, "Fac")
    nF = noise(-1250, -300, 2.2, 1.0)
    rF = rampn(nt, [(0.0, (0.95, 0.95, 0.97)), (1.0, (1.05, 1.05, 1.03))], -1050, -300)
    lk(nt, nF, "Fac", rF, "Fac")
    alb = rL
    for src in (rV, rM, rF):
        mx = nd(nt, "ShaderNodeMixRGB", -800, 300); mx.blend_type = 'MULTIPLY'
        mx.inputs[0].default_value = 1.0
        lk(nt, alb, "Color", mx, 1); lk(nt, src, "Color", mx, 2)
        alb = mx
    base_mix = nd(nt, "ShaderNodeMixRGB", -500, 300); base_mix.blend_type = 'MULTIPLY'
    base_mix.inputs[0].default_value = 1.0
    lk(nt, vc, "Color", base_mix, 1); lk(nt, alb, "Color", base_mix, 2)
    lk(nt, base_mix, "Color", bsdf, "Base Color")

    # ---- roughness: glossy back -> matte belly, mottle-varied ---------
    d_belly = mathn(nt, 'ABSOLUTE', -1250, -600)
    sub1 = mathn(nt, 'SUBTRACT', -1400, -600, v1=0.5)
    lk(nt, U, "Value", sub1, 0); lk(nt, sub1, "Value", d_belly, 0)
    belly_r = nd(nt, "ShaderNodeMapRange", -1050, -600)
    for nm_, vv in (("From Min", 0.0), ("From Max", 0.5), ("To Min", 1.0), ("To Max", 0.0)):
        belly_r.inputs[nm_].default_value = vv
    belly_r.clamp = True
    lk(nt, d_belly, "Value", belly_r, "Value")
    rough0 = mathn(nt, 'MULTIPLY_ADD', -850, -600, v1=0.20, v2=0.34)
    lk(nt, belly_r, "Result", rough0, 0)
    rough_v = mathn(nt, 'MULTIPLY_ADD', -650, -550, v1=0.10, v2=-0.05)
    lk(nt, nM, "Fac", rough_v, 0)
    rough_s = mathn(nt, 'ADD', -450, -600)
    lk(nt, rough0, "Value", rough_s, 0); lk(nt, rough_v, "Value", rough_s, 1)
    rough_hi = mathn(nt, 'MINIMUM', -250, -600, v1=0.68)
    lk(nt, rough_s, "Value", rough_hi, 0)
    rough_c = mathn(nt, 'MAXIMUM', -100, -600, v1=0.24)
    lk(nt, rough_hi, "Value", rough_c, 0)
    lk(nt, rough_c, "Value", bsdf, "Roughness")

    # ---- height: longitudinal creases (throat/belly) + micro grain ----
    wob = noise(-1450, -950, 0.5, 2.0)
    wob_s = mathn(nt, 'MULTIPLY_ADD', -1250, -950, v1=2.6, v2=-1.3)
    lk(nt, wob, "Fac", wob_s, 0)
    ph = mathn(nt, 'MULTIPLY', -1250, -1100, v1=289.0)
    lk(nt, U, "Value", ph, 0)
    ph2 = mathn(nt, 'ADD', -1050, -1025)
    lk(nt, ph, "Value", ph2, 0); lk(nt, wob_s, "Value", ph2, 1)
    sine = mathn(nt, 'SINE', -900, -1025)
    lk(nt, ph2, "Value", sine, 0)
    wave = nd(nt, "ShaderNodeMapRange", -750, -1025)
    for nm_, vv in (("From Min", -1.0), ("From Max", 1.0), ("To Min", 0.0), ("To Max", 1.0)):
        wave.inputs[nm_].default_value = vv
    lk(nt, sine, "Value", wave, "Value")
    wave_p = mathn(nt, 'POWER', -600, -1025, v1=1.6)
    lk(nt, wave, "Result", wave_p, 0)
    belly_band = nd(nt, "ShaderNodeMapRange", -1050, -1250)
    for nm_, vv in (("From Min", 0.0), ("From Max", 0.34), ("To Min", 1.0), ("To Max", 0.0)):
        belly_band.inputs[nm_].default_value = vv
    belly_band.clamp = True
    lk(nt, d_belly, "Value", belly_band, "Value")
    throat = nd(nt, "ShaderNodeMapRange", -1050, -1400)
    for nm_, vv in (("From Min", 0.78), ("From Max", 0.88), ("To Min", 0.0), ("To Max", 1.0)):
        throat.inputs[nm_].default_value = vv
    throat.clamp = True
    lk(nt, V, "Value", throat, "Value")
    # crease strength along v: whisper mid-body, real pleats only on
    # the throat (v>0.8) - v5.1 fix for the "corduroy flank" read
    body_cr = nd(nt, "ShaderNodeMapRange", -850, -1520)
    for nm_, vv in (("From Min", 0.45), ("From Max", 0.80), ("To Min", 0.10), ("To Max", 0.35)):
        body_cr.inputs[nm_].default_value = vv
    body_cr.clamp = True
    lk(nt, V, "Value", body_cr, "Value")
    throat_s2 = mathn(nt, 'MULTIPLY', -850, -1330, v1=0.65)
    lk(nt, throat, "Result", throat_s2, 0)
    thr_s = mathn(nt, 'ADD', -700, -1400)
    lk(nt, body_cr, "Result", thr_s, 0); lk(nt, throat_s2, "Value", thr_s, 1)
    crease = mathn(nt, 'MULTIPLY', -450, -1150)
    lk(nt, wave_p, "Value", crease, 0)
    cb = mathn(nt, 'MULTIPLY', -450, -1300)
    lk(nt, belly_band, "Result", cb, 0); lk(nt, thr_s, "Value", cb, 1)
    lk(nt, cb, "Value", crease, 1)
    crease_s = mathn(nt, 'MULTIPLY', -300, -1150, v1=0.85)
    lk(nt, crease, "Value", crease_s, 0)
    grain = noise(-1250, -1600, 7.0, 2.0)
    grain_s = mathn(nt, 'MULTIPLY', -1050, -1600, v1=0.13)
    lk(nt, grain, "Fac", grain_s, 0)
    hgt = mathn(nt, 'ADD', -150, -1250)
    lk(nt, crease_s, "Value", hgt, 0); lk(nt, grain_s, "Value", hgt, 1)
    bump = nd(nt, "ShaderNodeBump", 100, -1250)
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.26
    lk(nt, hgt, "Value", bump, "Height")
    lk(nt, bump, "Normal", bsdf, "Normal")

    # ---- plankton: clustered Voronoi bioluminescence ------------------
    one_u = mathn(nt, 'SUBTRACT', -1450, 900, v0=1.0)
    lk(nt, U, "Value", one_u, 1)
    dd = mathn(nt, 'MINIMUM', -1300, 850)
    lk(nt, U, "Value", dd, 0); lk(nt, one_u, "Value", dd, 1)
    dorsal = nd(nt, "ShaderNodeMapRange", -1150, 850)
    for nm_, vv in (("From Min", 0.0), ("From Max", 0.14), ("To Min", 1.0), ("To Max", 0.0)):
        dorsal.inputs[nm_].default_value = vv
    dorsal.clamp = True
    lk(nt, dd, "Value", dorsal, "Value")
    lat_abs = []
    for uu in (0.25, 0.75):
        s_ = mathn(nt, 'SUBTRACT', -1450, 1250, v1=uu)
        lk(nt, U, "Value", s_, 0)
        a_ = mathn(nt, 'ABSOLUTE', -1300, 1250)
        lk(nt, s_, "Value", a_, 0)
        lat_abs.append(a_)
    dlm = mathn(nt, 'MINIMUM', -1150, 1250)
    lk(nt, lat_abs[0], "Value", dlm, 0); lk(nt, lat_abs[1], "Value", dlm, 1)
    lat = nd(nt, "ShaderNodeMapRange", -1000, 1250)
    for nm_, vv in (("From Min", 0.0), ("From Max", 0.06), ("To Min", 0.85), ("To Max", 0.0)):
        lat.inputs[nm_].default_value = vv
    lat.clamp = True
    lk(nt, dlm, "Value", lat, "Value")
    gate_n = noise(-1450, 1450, 0.045, 2.0)
    gate = nd(nt, "ShaderNodeMapRange", -1250, 1450)
    for nm_, vv in (("From Min", 0.52), ("From Max", 0.72), ("To Min", 0.0), ("To Max", 0.40)):
        gate.inputs[nm_].default_value = vv
    gate.clamp = True
    lk(nt, gate_n, "Fac", gate, "Value")
    belly_ex = nd(nt, "ShaderNodeMapRange", -1050, 1450)
    for nm_, vv in (("From Min", 0.06), ("From Max", 0.16), ("To Min", 0.0), ("To Max", 1.0)):
        belly_ex.inputs[nm_].default_value = vv
    belly_ex.clamp = True
    lk(nt, d_belly, "Value", belly_ex, "Value")
    gate2 = mathn(nt, 'MULTIPLY', -900, 1450)
    lk(nt, gate, "Result", gate2, 0); lk(nt, belly_ex, "Result", gate2, 1)
    mask = mathn(nt, 'MAXIMUM', -750, 1000)
    lk(nt, dorsal, "Result", mask, 0); lk(nt, lat, "Result", mask, 1)
    mask2 = mathn(nt, 'MAXIMUM', -600, 1000)
    lk(nt, mask, "Value", mask2, 0); lk(nt, gate2, "Value", mask2, 1)
    pf1 = nd(nt, "ShaderNodeMapRange", -1450, 1650)
    for nm_, vv in (("From Min", 0.012), ("From Max", 0.05), ("To Min", 0.0), ("To Max", 1.0)):
        pf1.inputs[nm_].default_value = vv
    pf1.clamp = True
    lk(nt, V, "Value", pf1, "Value")
    pf2 = nd(nt, "ShaderNodeMapRange", -1250, 1650)
    for nm_, vv in (("From Min", 0.955), ("From Max", 0.99), ("To Min", 1.0), ("To Max", 0.0)):
        pf2.inputs[nm_].default_value = vv
    pf2.clamp = True
    lk(nt, V, "Value", pf2, "Value")
    polef = mathn(nt, 'MULTIPLY', -1050, 1650)
    lk(nt, pf1, "Result", polef, 0); lk(nt, pf2, "Result", polef, 1)

    def dot_layer(x, y, scale, d0, d1, weight):
        vn = voro(x, y, scale)
        dm = nd(nt, "ShaderNodeMapRange", x + 200, y)
        for nm_, vv in (("From Min", d0), ("From Max", d1), ("To Min", 1.0), ("To Max", 0.0)):
            dm.inputs[nm_].default_value = vv
        dm.clamp = True
        lk(nt, vn, "Distance", dm, "Value")
        bw = nd(nt, "ShaderNodeRGBToBW", x + 200, y - 150)
        lk(nt, vn, "Color", bw, "Color")
        iv = nd(nt, "ShaderNodeMapRange", x + 400, y - 150)
        for nm_, vv in (("From Min", 0.0), ("From Max", 1.0), ("To Min", 0.35), ("To Max", 1.0)):
            iv.inputs[nm_].default_value = vv
        lk(nt, bw, "Val", iv, "Value")
        o1 = mathn(nt, 'MULTIPLY', x + 600, y)
        lk(nt, dm, "Result", o1, 0); lk(nt, iv, "Result", o1, 1)
        o2 = mathn(nt, 'MULTIPLY', x + 750, y, v1=weight)
        lk(nt, o1, "Value", o2, 0)
        return o2
    dotsA = dot_layer(-1450, -1850, 1.5, 0.02, 0.10, 1.0)
    dotsB = dot_layer(-1450, -2250, 0.8, 0.04, 0.20, 0.55)
    dots = mathn(nt, 'MAXIMUM', -450, -2000)
    lk(nt, dotsA, "Value", dots, 0); lk(nt, dotsB, "Value", dots, 1)
    dots_m = mathn(nt, 'MULTIPLY', -300, -2000)
    lk(nt, dots, "Value", dots_m, 0); lk(nt, mask2, "Value", dots_m, 1)
    dots_f = mathn(nt, 'MULTIPLY', -150, -2000)
    lk(nt, dots_m, "Value", dots_f, 0); lk(nt, polef, "Value", dots_f, 1)
    col_n = noise(-1450, -2600, 0.22, 2.0)
    col_f = nd(nt, "ShaderNodeMapRange", -1250, -2600)
    for nm_, vv in (("From Min", 0.50), ("From Max", 0.72), ("To Min", 0.0), ("To Max", 1.0)):
        col_f.inputs[nm_].default_value = vv
    col_f.clamp = True
    lk(nt, col_n, "Fac", col_f, "Value")
    dot_col = nd(nt, "ShaderNodeMixRGB", -1000, -2600)
    dot_col.inputs[1].default_value = (0.45, 0.85, 1.0, 1.0)
    dot_col.inputs[2].default_value = (1.0, 0.70, 0.28, 1.0)
    lk(nt, col_f, "Result", dot_col, 0)
    inten = nd(nt, "ShaderNodeCombineXYZ", -100, -2150)
    lk(nt, dots_f, "Value", inten, "X"); lk(nt, dots_f, "Value", inten, "Y")
    lk(nt, dots_f, "Value", inten, "Z")
    emis = nd(nt, "ShaderNodeVectorMath", 50, -2300); emis.operation = 'MULTIPLY'
    lk(nt, dot_col, "Color", emis, 0); lk(nt, inten, "Vector", emis, 1)
    lk(nt, emis, "Vector", bsdf, "Emission Color")
    bsdf.inputs["Emission Strength"].default_value = 1.0
    return m

skin_proc = build_skin_proc()
skin_proc.use_fake_user = True

# ------------------------------------------------------------------ bake
BAKE_W, BAKE_H = 4096, 2048
def bake_image(name, colorspace):
    img = bpy.data.images.new(name, BAKE_W, BAKE_H, alpha=False)
    return img, colorspace

bpy.context.view_layer.objects.active = body
body.select_set(True)
for o in bpy.context.collection.objects:
    if o != body: o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 2   # colour/emit/rough/normal bakes are sample-invariant
sc.cycles.use_denoising = False
mesh.materials.clear(); mesh.materials.append(skin_proc)

def bake_pass(btype, img, pass_filter=None):
    nt = skin_proc.node_tree
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
    tn.location = (1700, -800)
    for n in nt.nodes: n.select = False
    tn.select = True; nt.nodes.active = tn
    kw = dict(type=btype, margin=12)
    if pass_filter: kw["pass_filter"] = pass_filter
    bpy.ops.object.bake(**kw)
    nt.nodes.remove(tn)
    print("BAKED", btype, img.name)

img_base, _ = bake_image("SkinTex", 'sRGB')
bake_pass('DIFFUSE', img_base, {'COLOR'})
img_rough, _ = bake_image("RoughTex", 'Non-Color')
bake_pass('ROUGHNESS', img_rough)
img_norm, _ = bake_image("NormalTex", 'Non-Color')
bake_pass('NORMAL', img_norm)
img_emis, _ = bake_image("PlanktonTex", 'sRGB')
bake_pass('EMIT', img_emis)
for o in bpy.context.collection.objects: o.hide_render = False

# pack FIRST, then assign colorspace (known quirk: colorspace first un-packs)
for img, csname in ((img_base, 'sRGB'), (img_emis, 'sRGB'),
                    (img_rough, 'Non-Color'), (img_norm, 'Non-Color')):
    img.pack()
    img.colorspace_settings.name = csname
    print("PACKED", img.name, img.packed_file is not None, img.colorspace_settings.name)

# ------------------------------------------------------- final skin material
skin = bpy.data.materials.new("WhaleSkin"); skin.use_nodes = True
nt = skin.node_tree; nt.nodes.clear()
out_n = nd(nt, "ShaderNodeOutputMaterial", 900, 0)
bsdf = nd(nt, "ShaderNodeBsdfPrincipled", 650, 0)
lk(nt, bsdf, "BSDF", out_n, "Surface")
tb = nd(nt, "ShaderNodeTexImage", -200, 300); tb.image = img_base
lk(nt, tb, "Color", bsdf, "Base Color")
tr = nd(nt, "ShaderNodeTexImage", -200, 0); tr.image = img_rough
lk(nt, tr, "Color", bsdf, "Roughness")
tnm = nd(nt, "ShaderNodeTexImage", -200, -300); tnm.image = img_norm
nm = nd(nt, "ShaderNodeNormalMap", 200, -300); nm.inputs["Strength"].default_value = 0.9
lk(nt, tnm, "Color", nm, "Color"); lk(nt, nm, "Normal", bsdf, "Normal")
te = nd(nt, "ShaderNodeTexImage", -200, -600); te.image = img_emis
lk(nt, te, "Color", bsdf, "Emission Color")
bsdf.inputs["Emission Strength"].default_value = 1.15
set_in(bsdf, "Subsurface Weight", 0.22)
set_in(bsdf, "Subsurface Radius", (0.55, 0.75, 1.05))
set_in(bsdf, "Subsurface Scale", 0.5)
set_in(bsdf, "Coat Weight", 0.15)
set_in(bsdf, "Coat Roughness", 0.38)
mesh.materials.clear(); mesh.materials.append(skin)

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

def prof1(keys, x):
    if x <= keys[0][0]: return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            s = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * (s * s * (3 - 2 * s))
    return keys[-1][1]

# tail flukes: grid-lofted foil, span +-8.8 (~0.22 x body length) - as v4
tc, ttan, te1, te2 = frame(0.0)
fspan = Vector((0, 0, 1)).cross(ttan); fspan.normalize()
fchord = ttan - fspan * ttan.dot(fspan); fchord.normalize()
fn = fchord.cross(fspan); fn.normalize()
if fn.dot(te1) < 0: fn = -fn          # fn = dorsal side
froot = tc - ttan * 0.4
LEAD_K  = [(0.0, 1.20), (3.0, 0.90), (5.8, 0.20), (7.8, -0.90), (8.8, -2.55)]
TRAIL_K = [(0.0, -0.05), (1.2, -0.92), (3.6, -1.28), (6.2, -1.72), (8.8, -2.65)]
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

# pectoral fins v5: LOFTED AIRFOIL sections (root thick -> tip thin,
# cambered) - the flat solidify plates of v4 are gone. Frame as v4:
# span swept back ~30 deg with slight dorsal dihedral, chord blended
# toward world-horizontal, broad teardrop planform ~9.6 long at t=0.78.
PEC_LEAD  = [(0.0, 1.35), (1.2, 1.90), (2.8, 2.15), (4.6, 1.90),
             (6.6, 1.40), (8.4, 0.70), (9.6, -0.05)]
PEC_TRAIL = [(0.0, -1.20), (1.8, -1.70), (4.0, -1.75), (6.4, -1.40),
             (8.6, -0.75), (9.6, -0.05)]
def airfoil_fin(name, origin, span, chord, nrm, material):
    NS, NA = 26, 9
    vs, fs = [], []
    for side in (1, -1):
        for i in range(NS):
            a = 9.6 * (i / (NS - 1))
            al, at = prof1(PEC_LEAD, a), prof1(PEC_TRAIL, a)
            tmax = 0.36 + (0.10 - 0.36) * (a / 9.6)
            for j in range(NA):
                s = j / (NA - 1)
                cpos = al + (at - al) * s
                th = tmax * (0.30 + 0.70 * math.sin(math.pi * s)) * 0.5
                cam = 0.10 * math.sin(math.pi * s) * (1.0 - 0.4 * (a / 9.6))
                p = origin + span * a + chord * cpos + nrm * (cam + side * th)
                p = p + Vector((0, 0, -0.018 * a))
                vs.append(tuple(p))
    for i in range(NS - 1):
        for j in range(NA - 1):
            a0 = i * NA + j; b0 = a0 + NA
            fs.append((a0, b0, b0 + 1, a0 + 1))
            c0 = NS * NA + a0; d0 = NS * NA + b0
            fs.append((c0, c0 + 1, d0 + 1, d0))
    for i in range(NS - 1):
        t0, t1 = i * NA, (i + 1) * NA
        b0, b1 = NS * NA + t0, NS * NA + t1
        fs.append((t0, b0, b1, t1))
        t0, t1 = i * NA + NA - 1, (i + 1) * NA + NA - 1
        b0, b1 = NS * NA + t0, NS * NA + t1
        fs.append((t0, t1, b1, b0))
    for j in range(NA - 1):
        t0 = (NS - 1) * NA + j; b0 = NS * NA + t0
        fs.append((t0, b0, b0 + 1, t0 + 1))
        fs.append((j, j + 1, NS * NA + j + 1, NS * NA + j))
    m = bpy.data.meshes.new(name + "Mesh"); m.from_pydata(vs, [], fs); m.update()
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    return finish(o, material)

for s, nm in ((1, "PecFinR"), (-1, "PecFinL")):
    c, tan, e1, e2 = frame(0.78)
    R = radius(0.78)
    base = c + e2 * (s * R * 0.70) + e1 * (-R * 0.34)
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
    nrm = span.cross(chord); nrm.normalize()
    airfoil_fin(nm, base, span, chord, nrm, FIN_M)

# dorsal fin at t=0.30 + smaller trailing bump at t=0.14 (as v4)
c, tan, e1, e2 = frame(0.30)
R = radius(0.30)
DOR = [(0.0, 0.0), (0.80, 1.40), (1.60, 2.20), (2.30, 1.70), (3.40, 0.0)]
world_outline("DorsalMain", c + e1 * (R * 0.90), -tan, e1, DOR, 0.16, FIN_M2)
c, tan, e1, e2 = frame(0.14)
R = radius(0.14)
DOR2 = [(0.0, 0.0), (0.45, 0.70), (0.95, 0.95), (1.35, 0.60), (1.90, 0.0)]
world_outline("DorsalRear", c + e1 * (R * 0.90), -tan, e1, DOR2, 0.12, FIN_M2)
# dorsal ridge: low lofted crest along the back, t=0.08..0.30 (as v4)
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
# iris texture: small canvas with radial golden gradient + fibrous
# radial streaks + dark collarette and rim (drawn in polar space)
def make_iris_image():
    S = 256
    px = [0.0] * (S * S * 4)
    def grad(r):
        stops = [(0.0, (1.00, 0.80, 0.32)), (0.30, (0.92, 0.60, 0.15)),
                 (0.62, (0.66, 0.38, 0.08)), (0.90, (0.42, 0.24, 0.045)),
                 (1.0, (0.16, 0.09, 0.015))]
        for (r0, c0), (r1, c1) in zip(stops, stops[1:]):
            if r <= r1:
                return lerp3(c0, c1, (r - r0) / (r1 - r0))
        return stops[-1][1]
    for y in range(S):
        for x in range(S):
            dx = (x - S / 2) / (S / 2); dy = (y - S / 2) / (S / 2)
            r = math.sqrt(dx * dx + dy * dy)
            th = math.atan2(dy, dx)
            col = grad(min(1.0, r))
            st = 0.5 + 0.5 * math.sin(th * 36 + 2.2 * math.sin(th * 7 + r * 5.0))
            st2 = 0.5 + 0.5 * math.sin(th * 13 - r * 9.0)
            f = 0.82 + 0.30 * st * (1.0 - 0.45 * r) + 0.10 * st2
            col = tuple(c * f for c in col)
            ring = math.exp(-((r - 0.34) / 0.05) ** 2)   # collarette
            col = tuple(c * (1.0 - 0.35 * ring) for c in col)
            if r > 0.93:                                  # dark outer rim
                col = lerp3(col, (0.10, 0.055, 0.008), smooth(0.93, 1.0, r))
            idx = (y * S + x) * 4
            px[idx:idx + 4] = (*col, 1.0)
    img = bpy.data.images.new("IrisTex", S, S, alpha=False)
    img.pixels = px
    img.pack()   # pack BEFORE colorspace (quirk)
    img.colorspace_settings.name = 'sRGB'
    return img

_iris_img = make_iris_image()
IRIS_M = bpy.data.materials.new("Iris"); IRIS_M.use_nodes = True
_int = IRIS_M.node_tree
_ib = _int.nodes["Principled BSDF"]
_itx = _int.nodes.new("ShaderNodeTexImage"); _itx.image = _iris_img
_int.links.new(_itx.outputs["Color"], _ib.inputs["Base Color"])
_int.links.new(_itx.outputs["Color"], _ib.inputs["Emission Color"])
_ib.inputs["Emission Strength"].default_value = 0.30
_ib.inputs["Roughness"].default_value = 0.25

def eye_cap(name, center, out_dir, R, cap_r, lift, material):
    """Spherical cap hugging a sphere of radius R around `center`,
    angular radius asin(cap_r/R), lifted `lift` along the normals.
    UVs are planar-radial (centre 0.5,0.5 - edge r=1) for the iris art."""
    up = Vector((0, 0, 1)) if abs(out_dir.z) < 0.9 else Vector((0, 1, 0))
    ax = out_dir.cross(up); ax.normalize()
    ay = out_dir.cross(ax); ay.normalize()
    NR, NS = 5, 28
    amax = math.asin(min(1.0, cap_r / R))
    samax = math.sin(amax)
    vs, uvs, fs = [], [], []
    for i in range(NR + 1):
        a = amax * i / NR
        sa, ca = math.sin(a), math.cos(a)
        for j in range(NS + 1):
            ph = 2 * math.pi * (j % NS) / NS
            dirv = out_dir * ca + (ax * math.cos(ph) + ay * math.sin(ph)) * sa
            vs.append(tuple(center + dirv * (R + lift)))
            uvs.append((0.5 + 0.5 * (sa / samax) * math.cos(ph),
                        0.5 + 0.5 * (sa / samax) * math.sin(ph)))
    for i in range(NR):
        for j in range(NS):
            a0 = i * (NS + 1) + j; b0 = a0 + NS + 1
            fs.append((a0, b0, b0 + 1, a0 + 1))
    m = bpy.data.meshes.new(name + "Mesh"); m.from_pydata(vs, [], fs); m.update()
    uvl = m.uv_layers.new(name="UVMap")
    for poly in m.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[m.loops[li].vertex_index]
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    return finish(o, material)

# eyes v5: eyeball sunk into the carved socket, iris disc (radial
# texture), pupil disc, TRANSPARENT CORNEA dome over the front
ec, etan, ee1, ee2 = frame(0.925)
ER = radius(0.925)
esx, esz = ring_scale(0.925)
for s, nm in ((1, "R"), (-1, "L")):
    # v5.2 EYE ANCHOR FIX: the v4 anchor sat at ~0.76R from the body
    # axis (inside the body), so the whole eye stack was buried ~1 unit
    # under the skin and only the pupil area poked out. Compute the
    # TRUE surface point along the same ring direction (ellipse ray
    # factor lam) and anchor the stack on it.
    ring = ee2 * (s * ER * esz * 0.80) + ee1 * (-ER * 0.06)
    lam = 1.0 / math.sqrt((0.06 / esx) ** 2 + 0.80 ** 2)
    ep = ec + ring * lam + etan * (ER * 0.24)
    out_dir = (ee2 * s * 0.92 + ee1 * (-0.06) + etan * 0.38); out_dir.normalize()
    q = out_dir.to_track_quat('Z', 'Y')
    # v5.1 EYE SINK: the v5 stack still stood ~0.5 proud of the
    # socket at side angles, reading as a mounted button. The WHOLE
    # assembly (rim / eyeball / iris / pupil / cornea) is sunk 0.25
    # deeper along out_dir; the cornea dome still clears the skin so
    # the wet gloss reads from the front.
    # socket rim sits DEEP and flat, fully under the dented skin: it
    # only plugs the gap between eyeball and skin at grazing angles
    # (v5.2 first pass had it proud, reading as a blue bezel ring)
    rim = sphere(f"EyeSocket{nm}", tuple(ep - out_dir * 0.69), (1.10, 1.10, 0.26), SOCKET_M, seg=24, rings=16)
    rim.rotation_mode = 'QUATERNION'; rim.rotation_quaternion = q
    # eyeball sunk into the carved socket so the visible cap is a
    # shallow wet dome (whale eyes sit nearly flush), not a ball.
    # Iris / pupil are SPHERICAL CAPS hugging the eyeball (a flat disc
    # would be pierced by the sphere at its centre).
    eye_c = ep - out_dir * 0.93
    sphere(f"Eyeball{nm}", tuple(eye_c), (1.02,) * 3, EYEBALL_M, seg=32, rings=22)
    eye_cap(f"Iris{nm}", eye_c, out_dir, 1.02, 0.54, 0.012, IRIS_M)
    eye_cap(f"Pupil{nm}", eye_c, out_dir, 1.02, 0.26, 0.024, PUPIL_M)
    sphere(f"Cornea{nm}", tuple(ep - out_dir * 0.90), (1.06,) * 3, CORNEA_M, seg=28, rings=20)
    # mouth line: on the surface from the snout back ~0.10 x L (as v4)
    # v5.1 MOUTH ANCHOR FIX: the v4 points used the raw ellipse coords
    # (A, B) = (-(0.05+0.30f)*0.99, s*0.985), whose norm grows past 1
    # toward the rear end (A^2+B^2 = 1.09 at f=1), so the rear of the
    # tube floated ~0.2 off the skin and ended in a visible open cut.
    # Each point is now projected onto the true loft ellipse (the same
    # ray-surface solution as the eye anchor above), nested 0.03 into
    # the carved mouth crease, and the per-point radius tapers the
    # bevel to ~0 at BOTH ends so the line fades into the skin.
    pts, rads = [], []
    for k in range(31):
        f = k / 30
        tt = 0.997 - 0.102 * f
        c, tan, e1, e2 = frame(tt)
        R = radius(tt)
        sx, sz = ring_scale(tt)
        A = -(0.05 + 0.30 * f) * 0.99
        B = s * 0.985
        lam = 1.0 / math.sqrt(A * A + B * B)
        off = e1 * (R * sx * A * lam) + e2 * (R * sz * B * lam)
        pts.append(tuple(c + off - off.normalized() * 0.03))
        rads.append(max(0.03, min(1.0, f / 0.14, (1.0 - f) / 0.20)))
    cu = bpy.data.curves.new(f"Mouth{nm}", 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = 0.06; cu.bevel_resolution = 2
    spl = cu.splines.new('POLY'); spl.points.add(len(pts) - 1)
    for p, co, rr in zip(spl.points, pts, rads):
        p.co = (*co, 1.0); p.radius = rr
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
glb_path = os.path.join(OUT, "sorakujira.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB",
                              export_apply=True, export_image_format='WEBP',
                              export_image_quality=90)
except TypeError as e:
    print("WEBP export kwargs rejected, falling back to AUTO:", e)
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB",
                              export_apply=True)
print("GLB SIZE MB:", round(os.path.getsize(glb_path) / 1e6, 2))
print("SORAKUJIRA V5 DONE")
