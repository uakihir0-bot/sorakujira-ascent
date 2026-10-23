"""Prop kit for SORAKUJIRA — 14 handcrafted landmark/prop meshes.

Builds assets/props.blend + assets/props.glb. The game finds meshes in the
GLB BY OBJECT NAME and clones them, so names are a fixed contract:
  coral_tree, shell_spire, rock_spire, shell_arch, bone_rib, bone_wheel,
  rib_gate, crystal_cluster_big, crystal_gate, stone_pillar, ruin_gate,
  aurora_ribbon, moon_crescent, halo_ring

Origins: base center (z=0) for landmarks; center for bone_wheel,
aurora_ribbon, halo_ring. Canvas textures are packed BEFORE save and their
colorspace is assigned AFTER pack (project rule).
"""
import bpy, math, os, random
import numpy as np
from array import array as farray
from mathutils import Vector, Matrix

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
RNG = random.Random(20261023)
NPR = np.random.default_rng(20261023)

# ---------------------------------------------------------------- textures
def _paint(w, h, fn):
    """fn(u, v, rng) -> (h, w, 4) float array. Row 0 = v=0 (bottom)."""
    yy, xx = np.mgrid[0:h, 0:w]
    u = xx / max(w - 1, 1)
    v = yy / max(h - 1, 1)
    return fn(u, v)

def canvas(name, w, h, fn):
    img = bpy.data.images.new(name, w, h, alpha=True)
    arr = _paint(w, h, fn).astype(np.float32)
    img.pixels.foreach_set(farray('f', arr.ravel()))
    img.pack()                                    # pack BEFORE save
    img.colorspace_settings.name = 'sRGB'         # colorspace AFTER pack
    return img

def _mix(c0, c1, t):
    t = np.clip(t, 0.0, 1.0)[..., None]
    return np.array(c0) * (1 - t) + np.array(c1) * t

def _rgba(rgb, a=1.0):
    h, w = rgb.shape[:2]
    out = np.ones((h, w, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a
    return out

def _speckle(shape, amp=0.05, seed=1):
    r = np.random.default_rng(seed)
    return (r.random(shape) - 0.5) * 2 * amp

def coral_paint(u, v):
    rgb = _mix((0.60, 0.22, 0.29), (0.94, 0.40, 0.42), v * 1.6)
    rgb = _mix(rgb, (1.00, 0.63, 0.34), np.clip((v - 0.55) * 1.8, 0, 1))
    rgb = _mix(rgb, (1.00, 0.80, 0.55), np.clip((v - 0.85) * 4.0, 0, 1))
    rgb += _speckle(u.shape, 0.045, 11)[..., None]
    rgb += (0.05 * np.sin(u * 90 + v * 6))[..., None]
    dots = (np.random.default_rng(3).random(u.shape) > 0.9965)
    rgb[dots] += 0.25
    return _rgba(np.clip(rgb, 0, 1))

def shell_paint(u, v):
    band = 0.5 + 0.5 * np.sin(v * 46 + 2.2 * np.sin(u * math.tau) + 1.2 * np.sin(v * 9))
    rgb = _mix((0.93, 0.83, 0.76), (0.95, 0.70, 0.72), band)
    rgb = _mix(rgb, (0.80, 0.76, 0.93), np.clip(0.5 + 0.5 * np.sin(u * math.tau * 2 + v * 14), 0, 1) * 0.35)
    rgb += (0.05 * np.sin(u * math.tau * 7 + v * 30))[..., None]     # pearlescent shimmer
    rgb += _speckle(u.shape, 0.03, 21)[..., None]
    return _rgba(np.clip(rgb, 0, 1))

def rock_paint(u, v):
    strata = np.sin(v * 54 + 3.0 * np.sin(u * math.tau * 3) + 2.0 * np.sin(v * 13))
    rgb = _mix((0.40, 0.39, 0.50), (0.58, 0.56, 0.68), 0.5 + 0.5 * strata)
    rgb *= (1 - 0.30 * np.clip(strata - 0.25, 0, 1))[..., None]
    rgb *= (1 - 0.18 * np.clip(-strata - 0.3, 0, 1))[..., None]
    rgb += _speckle(u.shape, 0.075, 31)[..., None]
    rgb += (0.05 * np.sin(u * math.tau * 9 + v * 22))[..., None]
    return _rgba(np.clip(rgb, 0, 1))

def _draw_cracks(arr, count=16, seed=5):
    """Darken thin random polylines (cracks) on an RGB float array (h,w,3+)."""
    h, w = arr.shape[:2]
    rng = random.Random(seed)
    dark = np.array((0.42, 0.37, 0.30))
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = rng.uniform(0, math.tau)
        for _s in range(rng.randint(14, 42)):
            ang += rng.uniform(-0.55, 0.55)
            x += math.cos(ang) * rng.uniform(3, 8)
            y += math.sin(ang) * rng.uniform(3, 8)
            xi, yi = int(x), int(y)
            x0, x1 = max(xi - 2, 0), min(xi + 3, w)
            y0, y1 = max(yi - 2, 0), min(yi + 3, h)
            if x0 >= x1 or y0 >= y1:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
            m = np.clip(1.2 - d, 0, 1) * 0.5
            arr[y0:y1, x0:x1, :3] = arr[y0:y1, x0:x1, :3] * (1 - m[..., None]) + dark * m[..., None]
    return arr

def bone_paint(u, v):
    rgb = _mix((0.90, 0.85, 0.74), (0.96, 0.93, 0.84), v)
    rgb += (0.035 * np.sin(u * math.tau * 5 + v * 40))[..., None]     # faint grain streaks
    rgb += _speckle(u.shape, 0.025, 41)[..., None]
    edge = np.clip(np.minimum(v, 1 - v) * 6, 0.75, 1.0)              # aged ends
    rgb *= edge[..., None]
    out = _rgba(np.clip(rgb, 0, 1))
    return _draw_cracks(out, 15, 7)

def _mossy(u, v, base, moss_bands, seed):
    rgb = _mix(np.array(base) * 0.92, np.array(base) * 1.08,
               0.5 + 0.5 * np.sin(u * math.tau * 4 + v * 18))
    rgb += _speckle(u.shape, 0.06, seed)[..., None]
    # warped (non-separable) noise -> blotches, not stripes
    n = np.sin(u * math.tau * 5 + 2.3 * np.sin(v * math.tau * 3 + 0.7)) \
        * np.sin(v * math.tau * 6 + 1.9 * np.sin(u * math.tau * 2 + 1.3))
    n = 0.5 + 0.5 * n
    n += 0.3 * np.sin(u * math.tau * 11 + v * 30) * np.sin(v * math.tau * 9 + u * 20)
    band = np.zeros_like(v)
    for c, s in moss_bands:
        band += np.exp(-((v - c) ** 2) / (2 * s * s))
    moss = np.clip((n - 0.78) * 3.0, 0, 1) * np.clip(band, 0, 1)
    rgb = _mix(rgb, (0.34, 0.55, 0.28), moss * 0.8)
    return rgb

def stone_paint(u, v):
    rgb = _mossy(u, v, (0.55, 0.56, 0.61), [(0.10, 0.10), (0.55, 0.13), (0.92, 0.09)], 51)
    return _rgba(np.clip(rgb, 0, 1))

def ruin_paint(u, v):
    rgb = _mossy(u, v, (0.47, 0.48, 0.52), [(0.06, 0.16), (0.45, 0.22), (0.85, 0.18)], 61)
    streak = np.clip(0.5 + 0.5 * np.sin(u * math.tau * 22 + 3 * np.sin(v * 8)), 0, 1)
    rgb *= (1 - 0.13 * streak * (1 - v))[..., None]                  # weather streaks
    rgb *= (0.72 + 0.28 * v)[..., None]                               # dark base
    out = _rgba(np.clip(rgb, 0, 1))
    return _draw_cracks(out, 10, 13)

def aurora_paint(u, v):
    rgb = _mix((0.22, 1.00, 0.60), (0.18, 0.82, 0.92), u * 1.5)
    rgb = _mix(rgb, (0.62, 0.40, 1.00), np.clip((u - 0.55) * 2.0, 0, 1))
    wisp = 0.85 + 0.15 * np.sin(u * 260 + 9 * np.sin(v * math.tau * 1.5))
    core = np.sin(math.pi * np.clip(v, 0, 1)) ** 0.55
    rgb *= (0.35 + 0.65 * core)[..., None] * wisp[..., None]
    a = (np.sin(math.pi * np.clip(u, 0, 1)) ** 0.6) * (np.sin(math.pi * np.clip(v, 0, 1)) ** 0.85)
    return _rgba(np.clip(rgb, 0, 1), np.clip(a, 0, 1) * 0.95)

IMG = {
    'coral':  canvas('CoralTex', 1024, 1024, coral_paint),
    'shell':  canvas('ShellTex', 1024, 1024, shell_paint),
    'rock':   canvas('RockTex', 1024, 1024, rock_paint),
    'bone':   canvas('BoneTex', 1024, 1024, bone_paint),
    'stone':  canvas('StoneTex', 1024, 1024, stone_paint),
    'ruin':   canvas('RuinTex', 1024, 1024, ruin_paint),
    'aurora': canvas('AuroraTex', 1024, 256, aurora_paint),
}

# ---------------------------------------------------------------- materials
def tex_mat(name, img, rough=0.6, emis_strength=0.0, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    if emis_strength > 0:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emis_strength
    if alpha:
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
        m.surface_render_method = 'BLENDED'
        if hasattr(m, 'use_backface_culling'):
            m.use_backface_culling = False
    return m

def plain_mat(name, color, rough=0.6, emission=None, es=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.05
    if emission is not None:
        b.inputs['Emission Color'].default_value = (*emission, 1.0)
        b.inputs['Emission Strength'].default_value = es
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'DITHERED'
    return m

MAT = {
    'coral':  tex_mat('CoralMat', IMG['coral'], rough=0.55),
    'shell':  tex_mat('ShellPearl', IMG['shell'], rough=0.32),
    'rock':   tex_mat('RockStrata', IMG['rock'], rough=0.95),
    'bone':   tex_mat('BoneMat', IMG['bone'], rough=0.7),
    'stone':  tex_mat('StoneMoss', IMG['stone'], rough=0.9),
    'ruin':   tex_mat('RuinStone', IMG['ruin'], rough=0.95),
    'aurora': tex_mat('AuroraMat', IMG['aurora'], rough=1.0, emis_strength=1.35, alpha=True),
    'crys_v': plain_mat('CrystalVioletBig', (0.55, 0.40, 0.95), rough=0.18,
                        emission=(0.45, 0.30, 1.0), es=0.55, alpha=0.94),
    'crys_vt': plain_mat('CrystalVioletTip', (0.72, 0.58, 1.00), rough=0.15,
                         emission=(0.55, 0.38, 1.0), es=1.25, alpha=0.94),
    'crys_c': plain_mat('CrystalCyanBig', (0.40, 0.85, 1.00), rough=0.18,
                        emission=(0.30, 0.75, 1.0), es=0.55, alpha=0.94),
    'crys_ct': plain_mat('CrystalCyanTip', (0.62, 0.95, 1.00), rough=0.15,
                         emission=(0.38, 0.85, 1.0), es=1.25, alpha=0.94),
    'darkrock': plain_mat('DarkRock', (0.20, 0.18, 0.30), rough=0.92),
    'grass':  plain_mat('MossGrass', (0.36, 0.58, 0.30), rough=1.0),
    'moon':   plain_mat('MoonGold', (0.98, 0.88, 0.58), rough=0.35,
                        emission=(1.0, 0.82, 0.45), es=0.5),
    'halo':   plain_mat('HaloGlow', (1.0, 0.96, 0.86), rough=0.3,
                        emission=(1.0, 0.93, 0.78), es=2.2),
    'halo_soft': plain_mat('HaloSoft', (1.0, 0.96, 0.86), rough=0.4,
                           emission=(1.0, 0.93, 0.78), es=0.8, alpha=0.16),
}

# ---------------------------------------------------------------- geometry
def prim_part(obj, mat, smooth=True):
    """Evaluated primitive -> part dict in world space; source object removed."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    mw = obj.matrix_world
    verts = [tuple(mw @ v.co) for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    uvs = [(0.0, 0.0)] * len(verts)
    if me.uv_layers.active:
        layer = me.uv_layers.active.data
        tmp = {}
        for loop in me.loops:
            tmp[loop.vertex_index] = tuple(layer[loop.index].uv)
        uvs = [tmp.get(i, (0.0, 0.0)) for i in range(len(verts))]
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(me)
    return {'verts': verts, 'faces': faces, 'uvs': uvs, 'mat': mat, 'smooth': smooth}

def _xform(part, matrix):
    part['verts'] = [tuple(matrix @ Vector(v)) for v in part['verts']]
    return part

def finalize(name, parts):
    verts, faces, uvs, smooth, face_mat = [], [], [], [], []
    mats = []
    for part in parts:
        base = len(verts)
        verts += part['verts']
        uvs += part.get('uvs') or [(0.0, 0.0)] * len(part['verts'])
        if part['mat'] not in mats:
            mats.append(part['mat'])
        mi = mats.index(part['mat'])
        for f in part['faces']:
            faces.append(tuple(base + i for i in f))
            smooth.append(part.get('smooth', True))
            face_mat.append(mi)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv_layer = me.uv_layers.new(name='UVMap')
    for loop in me.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
    for m in mats:
        me.materials.append(m)
    for poly, s, mi in zip(me.polygons, smooth, face_mat):
        poly.use_smooth = s
        poly.material_index = mi
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def _tube_frames(points, binormal):
    n = len(points)
    tangents = []
    for i in range(n):
        a = points[max(i - 1, 0)]; b = points[min(i + 1, n - 1)]
        t = b - a
        t.normalize()
        tangents.append(t)
    A_list, B_list = [], []
    if binormal is not None:
        B = binormal.normalized()
        for t in tangents:
            a = t.cross(B)
            if a.length < 1e-4:
                a = Vector((1, 0, 0))
            a.normalize()
            A_list.append(a); B_list.append(B.copy())
    else:  # parallel transport
        t0 = tangents[0]
        ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
        a = ref - t0 * ref.dot(t0)
        a.normalize()
        for t in tangents:
            a = a - t * a.dot(t)
            if a.length < 1e-5:
                a = Vector((1, 0, 0)) - t * t.x
            a.normalize()
            A_list.append(a.copy())
            B_list.append(t.cross(a).normalized())
    return A_list, B_list

def tube(points, radii, radial=10, binormal=None, w_scale=1.0, t_scale=1.0,
         mat=None, v_scale=1.0):
    """Tube along a 3D path with elliptical cross-section and capped ends."""
    n = len(points)
    A_list, B_list = _tube_frames(points, binormal)
    verts, faces, uvs = [], [], []
    for i, (p, r) in enumerate(zip(points, radii)):
        A, B = A_list[i], B_list[i]
        for j in range(radial):
            th = math.tau * j / radial
            off = A * (math.cos(th) * r * w_scale) + B * (math.sin(th) * r * t_scale)
            verts.append(tuple(p + off))
            uvs.append((j / radial, i / (n - 1) * v_scale))
    for i in range(n - 1):
        for j in range(radial):
            j1 = (j + 1) % radial
            a, b = i * radial + j, i * radial + j1
            c, d = (i + 1) * radial + j1, (i + 1) * radial + j
            faces.append((a, b, c, d))
    for end_i, flip in ((0, True), (n - 1, False)):
        ci = len(verts)
        verts.append(tuple(points[end_i]))
        uvs.append((0.5, end_i / (n - 1) * v_scale))
        ring = [end_i * radial + j for j in range(radial)]
        for j in range(radial):
            j1 = (j + 1) % radial
            faces.append((ci, ring[j1], ring[j]) if flip else (ci, ring[j], ring[j1]))
    return {'verts': verts, 'faces': faces, 'uvs': uvs, 'mat': mat, 'smooth': True}

def loft_vertical(profile, radial=16, mat=None, ridge=None):
    """Vertical loft. profile: list of (z, r, cx, cy, twist_rad)."""
    n = len(profile)
    verts, faces, uvs = [], [], []
    for i, (z, r, cx, cy, tw) in enumerate(profile):
        vf = i / (n - 1)
        for j in range(radial):
            th = math.tau * j / radial + tw
            rr = r * (ridge(th, vf) if ridge else 1.0)
            verts.append((cx + rr * math.cos(th), cy + rr * math.sin(th), z))
            uvs.append((j / radial, vf))
    for i in range(n - 1):
        for j in range(radial):
            j1 = (j + 1) % radial
            a, b = i * radial + j, i * radial + j1
            c, d = (i + 1) * radial + j1, (i + 1) * radial + j
            faces.append((a, b, c, d))
    for end_i, (z, r, cx, cy, tw), flip in ((0, profile[0], True), (n - 1, profile[-1], False)):
        if r < 0.02:
            continue
        ci = len(verts)
        verts.append((cx, cy, z))
        uvs.append((0.5, end_i / (n - 1)))
        ring = [end_i * radial + j for j in range(radial)]
        for j in range(radial):
            j1 = (j + 1) % radial
            faces.append((ci, ring[j1], ring[j]) if flip else (ci, ring[j], ring[j1]))
    return {'verts': verts, 'faces': faces, 'uvs': uvs, 'mat': mat, 'smooth': True}

def bezier(p0, p1, p2, n):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        q = (p0 * (1 - t) ** 2 + p1 * (2 * (1 - t) * t) + p2 * (t * t))
        pts.append(q)
    return pts

def noise3(x, y, z):
    return (math.sin(x * 2.9 + 1.7) * math.sin(y * 2.3 + 0.4) * math.sin(z * 2.6 + 2.1) * 0.55
            + math.sin(x * 5.7 + 0.3) * math.sin(y * 4.9 + 2.8) * math.sin(z * 5.1 + 0.9) * 0.30
            + math.sin(x * 11.3) * math.sin(y * 9.7) * math.sin(z * 10.1) * 0.15)

# ---------------------------------------------------------------- builders
def build_coral_tree():
    parts = []
    trunk_path = bezier(Vector((0, 0, 0)), Vector((0.25, 0.1, 3.2)), Vector((0.55, 0.2, 6.4)), 12)
    trunk_r = [0.62 * (1 - i / 11) + 0.13 * (i / 11) for i in range(12)]
    parts.append(tube(trunk_path, trunk_r, radial=12, mat=MAT['coral'], v_scale=1.4))
    def trunk_pt(f):
        i = min(int(f * 11), 10)
        return trunk_path[i].lerp(trunk_path[i + 1], f * 11 - i)
    branches = [  # (attach fraction, azimuth, length, radius)
        (0.42, 0.3, 3.4, 0.30), (0.55, 2.4, 3.0, 0.27), (0.66, 4.2, 2.8, 0.24),
        (0.78, 1.2, 2.4, 0.21), (0.86, 3.4, 2.1, 0.18), (0.97, 5.3, 1.8, 0.15),
    ]
    tips = []
    for f, az, L, r0 in branches:
        base = trunk_pt(f)
        d = Vector((math.cos(az), math.sin(az), 0))
        end = base + d * (L * 0.72) + Vector((0, 0, L * 0.78))
        ctrl = base + d * (L * 0.30) + Vector((0, 0, L * 0.42))
        path = bezier(base, ctrl, end, 9)
        radii = [r0 * (1 - i / 8) + 0.02 * (i / 8) for i in range(9)]
        parts.append(tube(path, radii, radial=9, mat=MAT['coral'], v_scale=0.9))
        tips.append((end, 0.10))
        for k, (sf, saz) in enumerate(((0.55, az + 0.8), (0.8, az - 0.7))):
            if (int(f * 100) + k) % 2 == 1:
                continue
            sb = path[min(int(sf * 8), 7)]
            sd = Vector((math.cos(saz), math.sin(saz), 0))
            sL = L * 0.38
            send = sb + sd * (sL * 0.6) + Vector((0, 0, sL * 0.75))
            sctrl = sb + sd * (sL * 0.25) + Vector((0, 0, sL * 0.4))
            spath = bezier(sb, sctrl, send, 7)
            sradii = [r0 * 0.55 * (1 - i / 6) + 0.015 * (i / 6) for i in range(7)]
            parts.append(tube(spath, sradii, radial=8, mat=MAT['coral'], v_scale=0.7))
            tips.append((send, 0.08))
    for pos, rr in tips:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rr, location=tuple(pos))
        parts.append(prim_part(bpy.context.object, MAT['coral']))
    return finalize('coral_tree', parts)

def build_shell_spire():
    prof = []
    N = 42
    for i in range(N):
        f = i / (N - 1)
        z = f * 8.2
        r = 1.45 * (1 - f) ** 0.72 + 0.05
        r *= 1 + 0.085 * math.sin(z * 2.1) * (1 - f * 0.6)        # whorl bumps
        cx = 0.38 * math.sin(f * math.pi * 0.62)
        prof.append((z, r, cx, 0.0, f * 2.3))
    ridge = lambda th, vf: 1 + 0.05 * math.cos(th * 7 - vf * 10.0)
    return finalize('shell_spire', [loft_vertical(prof, radial=28, mat=MAT['shell'], ridge=ridge)])

def build_rock_spire():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(0, 0, 0))
    rock = prim_part(bpy.context.object, MAT['rock'])
    jrng = random.Random(99)
    verts = []
    for (x, y, z) in rock['verts']:
        px, py, pz = x * 1.9, y * 1.55, (z * 0.5 + 0.5) * 9.0   # unit sphere -> 9m tall
        d = noise3(px * 0.55, py * 0.55, pz * 0.30) * 0.95 + jrng.uniform(-0.10, 0.10)
        rad = math.sqrt(px * px + py * py) or 1e-5
        px += px / rad * d; py += py / rad * d
        pz += noise3(px, py, pz * 0.2) * 0.35
        if pz > 7.55:                                            # flatten summit
            pz = 7.55 + (pz - 7.55) * 0.22
        if pz < 1.2:                                             # squash into a base
            pz *= 0.30
        verts.append((px, py, pz))
    rock['verts'] = verts
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1.35, depth=0.4,
                                        location=(0.1, 0.05, 7.62))
    grass = prim_part(bpy.context.object, MAT['grass'])
    return finalize('rock_spire', [rock, grass])

def build_shell_arch():
    parts = []
    for side in (-1, 1):
        prof = []
        N = 20
        for i in range(N):
            f = i / (N - 1)
            prof.append((f * 5.4, 0.62 - 0.20 * f, side * (2.75 - 0.55 * f), 0.0, f * 0.9))
        ridge = lambda th, vf: 1 + 0.06 * math.cos(th * 6)
        parts.append(loft_vertical(prof, radial=18, mat=MAT['shell'], ridge=ridge))
    pts, radii = [], []
    N = 18
    for i in range(N):
        f = i / (N - 1)
        phi = math.pi * (1 - f)
        pts.append(Vector((2.2 * math.cos(phi), 0, 5.15 + 2.05 * math.sin(phi))))
        radii.append(0.52 + 0.10 * math.sin(math.pi * f))
    parts.append(tube(pts, radii, radial=14, binormal=Vector((0, 1, 0)),
                      w_scale=1.65, t_scale=0.85, mat=MAT['shell'], v_scale=1.2))
    return finalize('shell_arch', parts)

def _rib_part(scale=1.0, y=0.0):
    pts, radii = [], []
    N = 26
    for i in range(N):
        f = i / (N - 1)
        th = math.pi * f
        pts.append(Vector((4.2 * math.cos(th) * scale, y, 9.8 * math.sin(th) * scale)))
        s = 0.45 + 0.62 * (math.sin(th) ** 0.75)
        radii.append(0.17 * s * (0.7 + 0.3 * scale))
    return tube(pts, radii, radial=12, binormal=Vector((0, 1, 0)),
                w_scale=1.9, t_scale=0.82, mat=MAT['bone'], v_scale=1.6)

def build_bone_rib():
    return finalize('bone_rib', [_rib_part(1.0)])

def build_rib_gate():
    return finalize('rib_gate', [_rib_part(0.92, -1.7), _rib_part(1.0, 0.0), _rib_part(0.92, 1.7)])

def build_bone_wheel():
    parts = []
    bpy.ops.mesh.primitive_torus_add(major_radius=3.2, minor_radius=0.30,
                                     major_segments=40, minor_segments=10, location=(0, 0, 0))
    parts.append(prim_part(bpy.context.object, MAT['bone']))
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.58, depth=0.55, location=(0, 0, 0))
    parts.append(prim_part(bpy.context.object, MAT['bone']))
    for k in range(6):
        a = math.tau * k / 6 + 0.26
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [d * 0.30, d * 1.65 + Vector((0, 0, 0.10)), d * 3.05]
        parts.append(tube(pts, [0.17, 0.145, 0.115], radial=8,
                          binormal=Vector((0, 0, 1)), mat=MAT['bone'], v_scale=0.8))
    stand = Matrix.Rotation(math.radians(-90), 4, 'X')   # ring XY -> XZ: stands upright
    return finalize('bone_wheel', [_xform(p, stand) for p in parts])

def _shard_parts(loc, height, radius, mat_main, mat_tip, tilt=(0, 0, 0)):
    """Elongated octahedron shard: bottom point + body + emissive tip cone."""
    parts = []
    h_bot, h_tip = height * 0.30, height * 0.26
    h_mid = height - h_bot - h_tip
    specs = [  # (radius1, radius2, depth, z_center, mat)
        (0.0, radius, h_bot, h_bot / 2, mat_main),
        (radius, radius * 0.36, h_mid, h_bot + h_mid / 2, mat_main),
        (radius * 0.36, 0.0, h_tip, h_bot + h_mid + h_tip / 2, mat_tip),
    ]
    for r1, r2, depth, zc, m in specs:
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r1, radius2=r2, depth=depth,
                                        location=(0, 0, zc))
        o = bpy.context.object
        o.rotation_euler = tilt
        # rigid tilt about the shard base point `loc`: center goes to loc + R @ (0,0,zc)
        o.location = Vector(loc) + (o.rotation_euler.to_matrix() @ Vector((0, 0, zc)))
        bpy.context.view_layer.update()
        parts.append(prim_part(o, m))
    return parts

def _rock_blob(loc, scale, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=loc)
    part = prim_part(bpy.context.object, mat)
    cx, cy, cz = loc
    verts = []
    for (x, y, z) in part['verts']:
        px, py, pz = (x - cx) * scale[0], (y - cy) * scale[1], (z - cz) * scale[2]
        d = noise3(px * 0.8 + cx, py * 0.8, pz * 0.8) * 0.22
        verts.append((cx + px * (1 + d), cy + py * (1 + d), cz + pz * (1 + d * 0.5)))
    part['verts'] = verts
    return part

def build_crystal_cluster_big():
    parts = [_rock_blob((0, 0, 0.30), (2.3, 2.3, 0.85), MAT['darkrock'])]
    shards = [  # (loc, height, radius, violet?)
        ((0.0, 0.0, 0.55), 4.6, 0.62, True), ((1.05, 0.45, 0.45), 3.4, 0.50, False),
        ((-1.0, 0.55, 0.45), 3.0, 0.46, False), ((-0.75, -0.85, 0.45), 2.5, 0.42, True),
        ((0.95, -0.75, 0.45), 2.2, 0.38, True), ((0.15, 1.15, 0.40), 1.8, 0.34, False),
    ]
    tilts = [(0.03, -0.02, 0), (-0.16, 0.12, 0), (0.10, -0.18, 0),
             (-0.20, -0.10, 0), (0.14, 0.16, 0), (-0.24, 0.04, 0)]
    for (loc, h, r, violet), tilt in zip(shards, tilts):
        mm = MAT['crys_v'] if violet else MAT['crys_c']
        mt = MAT['crys_vt'] if violet else MAT['crys_ct']
        parts += _shard_parts(loc, h, r, mm, mt, tilt)
    return finalize('crystal_cluster_big', parts)

def build_crystal_gate():
    parts = [_rock_blob((-1.65, 0, 0.15), (1.0, 1.0, 0.55), MAT['darkrock']),
             _rock_blob((1.65, 0, 0.15), (1.0, 1.0, 0.55), MAT['darkrock'])]
    lean = math.radians(13)
    parts += _shard_parts((-1.6, 0, 0.1), 7.2, 0.78, MAT['crys_v'], MAT['crys_vt'],
                          tilt=(0, lean, 0))
    parts += _shard_parts((1.6, 0, 0.1), 7.2, 0.78, MAT['crys_c'], MAT['crys_ct'],
                          tilt=(0, -lean, 0))
    return finalize('crystal_gate', parts)

def build_stone_pillar():
    prof = []
    N = 18
    for i in range(N):
        f = i / (N - 1)
        r = 1.12 * (1 - f) + 0.78 * f
        r *= 1 + 0.10 * math.sin(f * math.pi)
        prof.append((f * 8.0, r, 0.0, 0.0, 0.0))
    # chipped edges baked in as a radius-modulating ridge
    def ridge(th, vf):
        return 1 + 0.055 * math.sin(th * 5 + vf * 9) + 0.04 * math.sin(th * 11 - vf * 17) \
            + 0.03 * math.sin(th * 23 + vf * 31)
    return finalize('stone_pillar', [loft_vertical(prof, radial=16, mat=MAT['stone'], ridge=ridge)])

def _beveled_box(size, loc, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.rotation_euler = (0, 0, rot_z)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bev = o.modifiers.new('bev', 'BEVEL')
    bev.width = 0.13; bev.segments = 2
    bpy.context.view_layer.update()
    return o

def build_ruin_gate():
    parts = []
    tall = _beveled_box((1.35, 1.15, 6.4), (-1.95, 0, 3.2))
    parts.append(prim_part(tall, MAT['ruin'], smooth=False))
    broken = _beveled_box((1.35, 1.15, 5.1), (1.95, 0, 2.55))
    bp = prim_part(broken, MAT['ruin'], smooth=False)
    verts = []  # jagged broken top
    for (x, y, z) in bp['verts']:
        if z > 4.55:
            f = (z - 4.55) / 0.55
            z -= RNG.uniform(0.1, 0.62) * f
            x += RNG.uniform(-0.05, 0.05); y += RNG.uniform(-0.05, 0.05)
        verts.append((x, y, z))
    bp['verts'] = verts
    parts.append(bp)
    lintel = _beveled_box((5.9, 1.25, 0.95), (0.05, 0, 6.05))
    lintel.rotation_euler = (0, math.radians(-11), math.radians(2))
    bpy.context.view_layer.update()
    parts.append(prim_part(lintel, MAT['ruin'], smooth=False))
    parts.append(_rock_blob((-1.9, 0.9, 0.2), (0.8, 0.7, 0.45), MAT['ruin']))
    parts.append(_rock_blob((2.6, -0.8, 0.15), (0.6, 0.55, 0.35), MAT['ruin']))
    return finalize('ruin_gate', parts)

def build_aurora_ribbon():
    SEG_X, SEG_Y = 96, 8
    L, W = 24.0, 2.4
    verts, faces, uvs = [], [], []
    for i in range(SEG_X + 1):
        u = i / SEG_X
        x = (u - 0.5) * L
        yc = 1.7 * math.sin(x * 0.30 + 0.4)
        zc = 1.15 * math.sin(x * 0.20 + 1.2)
        for j in range(SEG_Y + 1):
            v = j / SEG_Y
            y = yc + (v - 0.5) * W * math.cos(x * 0.16)
            z = zc + (v - 0.5) * W * math.sin(x * 0.16) \
                + 0.38 * math.sin(u * math.tau * 4.5 + v * math.tau) * math.sin(math.pi * v)
            verts.append((x, y, z))
            uvs.append((u, v))
    for i in range(SEG_X):
        for j in range(SEG_Y):
            a = i * (SEG_Y + 1) + j; b = a + SEG_Y + 1
            faces.append((a, b, b + 1, a + 1))
    part = {'verts': verts, 'faces': faces, 'uvs': uvs, 'mat': MAT['aurora'], 'smooth': True}
    return finalize('aurora_ribbon', [part])

def build_moon_crescent():
    R, r = 3.0, 2.5
    C = Vector((1.05, 0.55))
    d = C.length
    a = (R * R - r * r + d * d) / (2 * d)
    h = math.sqrt(max(R * R - a * a, 0.0))
    e = C / d
    perp = Vector((-e.y, e.x))
    Bpt = e * a
    P1, P2 = Bpt + perp * h, Bpt - perp * h
    def ang(p, c):
        return math.atan2(p.y - c.y, p.x - c.x)
    a1o, a2o = ang(P1, Vector((0, 0))), ang(P2, Vector((0, 0)))
    end_o = a2o
    while end_o < a1o + math.pi:
        end_o += math.tau
    a2i, a1i = ang(P2, C), ang(P1, C)
    end_i = a1i
    while a2i - end_i < math.pi:
        end_i -= math.tau
    pts = []
    for i in range(45):
        t = a1o + (end_o - a1o) * i / 44
        pts.append(Vector((R * math.cos(t), R * math.sin(t))))
    for i in range(1, 37):
        t = a2i + (end_i - a2i) * i / 36
        pts.append(C + Vector((r * math.cos(t), r * math.sin(t))))
    rot = -0.45
    cr, sr = math.cos(rot), math.sin(rot)
    pts = [Vector((p.x * cr - p.y * sr, p.x * sr + p.y * cr)) for p in pts]
    curve = bpy.data.curves.new('MoonCurve', 'CURVE')
    curve.dimensions = '2D'
    curve.fill_mode = 'BOTH'
    curve.extrude = 0.17
    curve.bevel_depth = 0.045
    curve.bevel_resolution = 1
    sp = curve.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (co.x, co.y, 0.0, 1.0)
    sp.use_cyclic_u = True
    obj = bpy.data.objects.new('MoonCurveObj', curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    part = prim_part(obj, MAT['moon'])
    # curve lives in XY (flat); rotate +90 deg about X so the crescent stands
    # upright in the XZ plane, then lift so its base sits at z ~= 0.05
    _xform(part, Matrix.Rotation(math.radians(90), 4, 'X'))
    part['verts'] = [(x, y, z + 3.05) for (x, y, z) in part['verts']]
    return finalize('moon_crescent', [part])

def build_halo_ring():
    parts = []
    bpy.ops.mesh.primitive_torus_add(major_radius=4.0, minor_radius=0.085,
                                     major_segments=56, minor_segments=8, location=(0, 0, 0))
    parts.append(prim_part(bpy.context.object, MAT['halo']))
    bpy.ops.mesh.primitive_torus_add(major_radius=4.0, minor_radius=0.30,
                                     major_segments=56, minor_segments=10, location=(0, 0, 0))
    parts.append(prim_part(bpy.context.object, MAT['halo_soft']))
    stand = Matrix.Rotation(math.radians(-90), 4, 'X')   # ring XY -> XZ: stands upright
    return finalize('halo_ring', [_xform(p, stand) for p in parts])

# ---------------------------------------------------------------- main
BUILDERS = [
    ('coral_tree', build_coral_tree), ('shell_spire', build_shell_spire),
    ('rock_spire', build_rock_spire), ('shell_arch', build_shell_arch),
    ('bone_rib', build_bone_rib), ('bone_wheel', build_bone_wheel),
    ('rib_gate', build_rib_gate), ('crystal_cluster_big', build_crystal_cluster_big),
    ('crystal_gate', build_crystal_gate), ('stone_pillar', build_stone_pillar),
    ('ruin_gate', build_ruin_gate), ('aurora_ribbon', build_aurora_ribbon),
    ('moon_crescent', build_moon_crescent), ('halo_ring', build_halo_ring),
]

total = 0
for name, fn in BUILDERS:
    obj = fn()
    obj.data.calc_loop_triangles()
    tris = len(obj.data.loop_triangles)
    total += tris
    dims = obj.dimensions
    print(f"PROP {name}: {tris} tris, size {dims.x:.1f} x {dims.y:.1f} x {dims.z:.1f} m")
print(f"TOTAL TRIS: {total}")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'props.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'props.glb'), export_format='GLB')
print("PROPS DONE", os.path.getsize(os.path.join(OUT, 'props.glb')), "bytes GLB")
