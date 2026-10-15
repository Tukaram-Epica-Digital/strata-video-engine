"""Guion animado: reparto por capas (estilo Ollama/llama.cpp) vs expertos (Strata).
Arquitectura: primero se construye la geometria, se calcula su bounding box y la camara
se ajusta para que SIEMPRE quepa en el area segura del cuadro. Despues se rotula."""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import (Mesh, OPAQUE, ADD, norm, sc, hexc, spline, ease, smoothstep,
                    lerp, look_at, png_write)
from raster import Renderer, upscale_bilinear, TEX_GLOW, TEX_DOT
from props import (motherboard, gpu_card, cpu_block, ram_sticks, ssd_drive,
                   token3d, glow_quad, panel_z, _quad_bb,
                   AMBERL, GOLDL, HOTL, REDL, DIML, CYANL, ICEL)
from labels import Labels
from framing import fit_view
import bg as bgmod

FPS = 30
DUR = 60.0
NF = int(DUR * FPS)

T_INTRO = (0.0, 5.5)
T_A = (5.5, 25.0)
T_TRANS = (25.0, 27.5)
T_B = (27.5, 45.0)
T_VS = (45.0, 54.0)
T_END = (54.0, 60.0)

SAFE = (0.055, 0.945, 0.075, 0.925)


def ph(t, a, b):
    return np.clip((t - a) / max(1e-6, b - a), 0, 1)


def act(t, a, b, fi=0.4, fo=0.4):
    if t < a or t > b:
        return 0.0
    return min(smoothstep(a, a + fi, t), 1 - smoothstep(b - fo, b, t))


def corners(bb):
    x0, x1, y0, y1, z0, z1 = bb
    return np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])


def merge_bb(a, b):
    return (min(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]),
            min(a[4], b[4]), max(a[5], b[5]))


# ------------------------------------------------------------------ mosaico
EX_COLS, EX_ROWS = 128, 192   # 24576 expertos


def expert_panel(seed, n_active=8, hot_frac=0.16, pulse=0.0, hot_bias=0.55):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:EX_ROWS, 0:EX_COLS]
    base = np.full((EX_ROWS, EX_COLS), 0.05, np.float32)
    hot = np.clip(1.0 - (xx / (EX_COLS * hot_frac) + yy / (EX_ROWS * hot_bias)), 0, 1)
    base += hot * (0.26 + 0.20 * pulse)
    for k in range(n_active):
        r = int(rng.integers(0, EX_ROWS)); c = int(rng.integers(0, EX_COLS))
        base[r, c] = 1.0
        if r + 1 < EX_ROWS:
            base[r + 1, c] = 0.7
    return base


# ------------------------------------------------------------------ ESCENA A
def scene_A(mesh, r, t, off=(0, 0, 0), s=1.0):
    """modelo partido por capas: 8 en GPU, 6 en RAM, todo cruzando PCIe"""
    a = np.asarray(off, float)
    tt = max(0.0, t - T_A[0])
    gp = a + np.array([-5.4 * s, 0.0, 0.0])
    rp = a + np.array([6.2 * s, 0.0, -1.0])
    gpu_card(mesh, r, gp + np.array([0, 1.1 * s, 0]), t, w=7.0 * s, d=3.2 * s, load=0.8)
    vx, vy, vz = gp + np.array([0, 2.2 * s, 1.66 * s])
    for i in range(8):
        yy = vy + (3.2 - i * 0.78) * 0.30 * s
        mesh.box((vx, yy, vz), (5.4 * s, 0.34 * s, 0.05), AMBERL, 0.85)
    px, py, pz = rp + np.array([3.0 * s, 3.4 * s, -4.4 * s])
    for i in range(6):
        yy = py + (2.8 - i * 0.78) * 0.30 * s
        mesh.box((px, yy, pz), (5.4 * s, 0.34 * s, 0.05), DIML, 0.30)
    mesh.wire((px, py, pz), (5.9 * s, 4.4 * s, 0.02), sc(CYANL, 0.35), 0.02 * s)
    cpu_block(mesh, rp + np.array([-1.2 * s, 0.2, 0.4 * s]), t, glow=0.7)
    ram_sticks(mesh, rp[0] + 0.4 * s, rp[2] - 2.8 * s, n=4, glow=0.7, gap=0.8 * s, h=2.6 * s)
    p0 = gp + np.array([3.7 * s, 2.2 * s, 0])
    p1 = rp + np.array([-3.6 * s, 2.2 * s, 0])
    mid = (p0 + p1) * 0.5
    mesh.bar(p0, p1, 0.34 * s, hexc('2A1A1E'), 0.0, OPAQUE)
    mesh.bar(mid - (p1 - p0) * 0.05, mid + (p1 - p0) * 0.05, 0.15 * s, hexc('4A2A2E'), 0.0, OPAQUE)
    mesh.bar(p0, p1, 0.09 * s, REDL, 1.0, ADD)
    q = 1.0 - 0.2 * np.cos(tt * 1.3)
    for i in range(4):
        xx = mid[0] - (0.6 + i * 0.62) * s * q
        token3d(mesh, (xx, mid[1], mid[2]), REDL, 0.20 * s, 0.9)
    for i in range(4):
        u = ((tt * 0.85) + i / 4) % 1.0
        token3d(mesh, p0 + (mid - p0) * u, REDL, 0.13 * s, 0.7)
    path = []
    for i in range(8):
        path.append((vx - 2.5 * s, vy + (3.2 - i * 0.78) * 0.30 * s, vz + 0.42 * s))
    path += [tuple(p0), tuple(mid), tuple(p1)]
    for i in range(6):
        path.append((px - 2.5 * s, py + (2.8 - i * 0.78) * 0.30 * s, pz + 0.42 * s))
    pos = spline(path, (tt * 0.30) % 1.0)
    token3d(mesh, pos, HOTL, 0.30 * s, 1.0)
    glow_quad(mesh, pos, 2.4 * s, 2.4 * s, AMBERL, 0.4)
    bb = (gp[0] - 4.0 * s, rp[0] + 6.4 * s, 0.0, 6.2 * s, rp[2] - 4.8 * s, 2.6 * s)
    return {'bb': bb, 'gpu': gp, 'ram': rp, 'mid': mid, 'vram': (vx, vy, vz),
            'ram_pnl': (px, py, pz)}


# ------------------------------------------------------------------ ESCENA B
def scene_B(mesh, r, t, off=(0, 0, 0), s=1.0):
    """24.576 expertos: el router elige 8, los mas usados ya estan en la GPU"""
    a = np.asarray(off, float)
    tt = max(0.0, t - T_B[0])
    gp = a + np.array([-5.6 * s, 0.0, 0.0])
    rp = a + np.array([6.4 * s, 0.0, -1.0])
    gpu_card(mesh, r, gp + np.array([0, 1.1 * s, 0]), t, w=7.0 * s, d=3.2 * s, load=0.5)
    pulse = 0.5 + 0.5 * np.sin(tt * 4.0)
    step = int(tt * 6) % 6
    tg = r.tex(expert_panel(3 + step, 6, 0.55, pulse, 0.55))
    panel_z(mesh, gp + np.array([0, 2.2 * s, 1.66 * s]), 5.4 * s, 2.6 * s, tg)
    ta = r.tex(expert_panel(7 + step, 10, 0.10, pulse * 0.35, 0.10))
    px, py, pz = rp + np.array([2.8 * s, 3.4 * s, -4.6 * s])
    panel_z(mesh, (px, py, pz), 6.2 * s, 4.8 * s, ta, frame=CYANL)
    cpu_block(mesh, rp + np.array([-1.6 * s, 0.2, 0.4 * s]), t, glow=0.9)
    ram_sticks(mesh, rp[0] + 0.0 * s, rp[2] - 3.0 * s, n=4, glow=0.9, gap=0.8 * s, h=2.6 * s)
    ssd_drive(mesh, a[0] - 3.0 * s, a[2] + 5.6 * s, glow=0.4, L=5.6 * s)
    rp2 = a + np.array([0.0, 2.8 * s, 1.2 * s])
    mesh.wire(rp2, (1.2 * s, 1.2 * s, 1.2 * s), HOTL, 0.05 * s)
    _quad_bb(mesh, None, rp2, 2.0 * s, 2.0 * s, GOLDL, 0.85, 1.0, TEX_GLOW)
    u = (tt * 0.40) % 1.0
    pin = a + np.array([-11.0 * s, 2.8 * s, 1.2 * s])
    token3d(mesh, pin + (rp2 - pin) * min(1.0, u * 2.0), HOTL, 0.30 * s, 1.0)
    rng = np.random.default_rng(int(tt * 5))
    gpnl = gp + np.array([0, 2.2 * s, 1.72 * s])
    for k in range(8):
        if k < 5:
            tgt = gpnl + np.array([rng.uniform(-2.3, 2.3), rng.uniform(-1.1, 1.1), 0.1]) * s
        else:
            tgt = np.array([px, py, pz]) + np.array([rng.uniform(-2.6, 2.6), rng.uniform(-2.0, 2.0), 0.2]) * s
        f = ((tt * 1.4) + k * 0.125) % 1.0
        col = AMBERL if k < 5 else CYANL
        token3d(mesh, rp2 + (tgt - rp2) * f, col, 0.16 * s, 0.95)
        mesh.ribbon([rp2, (rp2 + tgt) * 0.5 + np.array([0, 1.0 * s, 0]), tgt], 0.05 * s, col,
                    alpha=np.array([0.0, 0.45, 0.0]))
    if u > 0.5:
        w = (u - 0.5) / 0.5
        token3d(mesh, rp2 + np.array([11.0 * s * w, 0.0, 0.0]), GOLDL, 0.28 * s, 1.0)
    bb = (gp[0] - 4.2 * s, rp[0] + 6.2 * s, 0.0, 6.2 * s, rp[2] - 5.0 * s, 5.9 * s)
    return {'bb': bb, 'gpu': gp, 'ram': rp, 'router': rp2, 'vram': gpnl, 'ram_pnl': (px, py, pz)}


# ------------------------------------------------------------------ orbita
def orbit(t):
    """direccion de camara (sin distancia: la calcula fit_view)"""
    if t < T_A[0]:
        p = ease(ph(t, *T_INTRO))
        ang = lerp(-1.05, -0.62, p); el = lerp(0.72, 0.44, p); fov = 42
    elif t < T_TRANS[0]:
        p = ph(t, *T_A)
        ang = lerp(-0.62, -0.26, p); el = lerp(0.44, 0.36, p) + 0.03 * np.sin(p * 6.0); fov = 40
    elif t < T_B[0]:
        p = ease(ph(t, *T_TRANS))
        ang = lerp(-0.26, 0.62, p); el = lerp(0.36, 0.42, p); fov = 40
    elif t < T_VS[0]:
        p = ph(t, *T_B)
        ang = lerp(0.62, 0.26, p); el = lerp(0.42, 0.36, p) + 0.03 * np.sin(p * 6.0); fov = 40
    elif t < T_END[0]:
        p = ph(t, *T_VS)
        ang = lerp(0.26, 0.0, p); el = lerp(0.36, 0.44, p); fov = 44
    else:
        p = ease(ph(t, *T_END))
        ang = 0.0; el = lerp(0.44, 0.38, p); fov = 44
    return ang, el, fov


# ------------------------------------------------------------------ frame
def build_frame(i, W, H, ss=1, no_bg=False):
    t = i / FPS
    ang, el, fov = orbit(t)
    u = np.array([np.sin(ang) * np.cos(el), np.sin(el), np.cos(ang) * np.cos(el)])

    r = Renderer(W, H, ss=ss,
                 lights=[{'dir': (-0.35, -1.0, -0.45), 'int': 1.10, 'col': np.ones(3)},
                         {'dir': (0.8, -0.35, 0.5), 'int': 0.30, 'col': hexc('FF7A30')},
                         {'dir': (-0.7, 0.2, -0.6), 'int': 0.20, 'col': hexc('3F7FD8')}],
                 ambient=0.20, rim=0.32, exposure=1.05, bloom=0.72, bloom_thr=0.46,
                 vignette=0.24, grain=0.006, fog_col=hexc('1A0508'), fog_k=0.028)
    mesh = Mesh()
    bbs = []
    info = {}
    if t < T_VS[0]:
        if t > T_A[0] - 0.6 and t < T_TRANS[0] + 0.8:
            info['A'] = scene_A(mesh, r, t); bbs.append(info['A']['bb'])
        if t > T_TRANS[0] - 0.4 and t < T_VS[0] + 0.8:
            info['B'] = scene_B(mesh, r, t); bbs.append(info['B']['bb'])
    else:
        info['A'] = scene_A(mesh, r, t, off=(-9.6, 0, 0), s=0.60)
        info['B'] = scene_B(mesh, r, t, off=(9.6, 0, 0), s=0.60)
        bbs = [merge_bb(info['A']['bb'], info['B']['bb'])]
    if not bbs:
        bbs = [(-11.6, 12.6, 0.0, 6.2, -5.8, 2.6)]
    bb = bbs[0]
    for b in bbs[1:]:
        bb = merge_bb(bb, b)
    pts = corners(bb)
    center = np.array([(bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2 * 0.85, (bb[4] + bb[5]) / 2])
    eye, tgt = fit_view(pts, center, u, fov, W, H, SAFE, dmin=4.0, dmax=70.0)
    motherboard(mesh, r)
    R, _ = look_at(eye, tgt)
    L = Labels(mesh, r, R, eye, tgt, fov, W, H)
    F = 0.030

    def put(key, pos, lines, color, mul=1.0, alpha=1.0, scale=3, panel=None):
        L.at(pos, lines, color, frac=F * mul, alpha=alpha, scale=scale, panel=panel)

    PN = sc(hexc('180408'), 1.0)
    PR = sc(hexc('2A0606'), 1.0)

    # ---- intro
    f = act(t, 0.6, T_A[0] + 0.2, 1.0, 0.6)
    if f > 0:
        c = np.array([(bb[0] + bb[1]) / 2, bb[3] * 1.15, bb[5]])
        put('i', c, ['UN MODELO DE 125 MIL MILLONES', 'DE PARAMETROS'], HOTL, 1.9, f, 4, PN)
        put('i', c - np.array([0, bb[3] * 0.30, 0]), ['EN UN PC GAMING NORMAL'], GOLDL, 1.3,
            f * 0.95, 3)

    # ---- escena A
    if 'A' in info and t < T_TRANS[0]:
        A = info['A']
        f = act(t, T_A[0] - 0.3, T_TRANS[0], 0.9, 0.7)
        if f > 0:
            gx, gy, gz = A['gpu']; rx, ry, rz = A['ram']
            put('A', (gx, 6.9, 2.2), ['REPARTO POR CAPAS'], ICEL, 1.35, f, 3)
            put('A', (gx, 6.0, 2.2), ['LO QUE HACE UN RUNNER TIPO OLLAMA'], GOLDL, 0.85, f * 0.9, 2)
            put('A', (gx, 5.0, 2.2), ['GPU 12 GB'], AMBERL, 0.8, f * 0.9, 2, sc(hexc('1A0608'), 1.0))
            put('A', (rx + 3.0, 7.6, -4.4), ['RAM 64 GB'], CYANL, 0.8, f * 0.9, 2, sc(hexc('1A0608'), 1.0))
            mx, my, mz = A['mid']
            put('A', (mx, my + 1.6, mz), ['PCIe 63 GB/S'], REDL, 0.75, f, 2)
        g = act(t, T_A[0] + 6.0, T_TRANS[0], 1.4, 0.7)
        if g > 0:
            mx, my, mz = A['mid']
            put('A', (mx, my - 1.8, mz + 3.2), ['EL MODELO NO CABE ENTERO'], REDL, 0.9, g, 2, PR)
            put('A', (mx, my - 2.6, mz + 3.2), ['LOS PESOS CRUZAN UNA Y OTRA VEZ'], REDL, 0.8,
                g * 0.9, 2)

    # ---- escena B
    if 'B' in info and T_TRANS[0] - 0.5 < t < T_VS[0] + 0.5:
        B = info['B']
        rx, ry, rz = B['ram']
        f = act(t, T_TRANS[0] - 0.3, T_VS[0] + 0.4, 0.9, 0.7)
        if f > 0:
            put('B', (rx + 2.8, 8.1, -4.6), ['REPARTO POR EXPERTOS'], HOTL, 1.35, f, 3)
            put('B', (rx + 2.8, 7.2, -4.6), ['LO QUE HACE STRATA'], GOLDL, 1.0, f * 0.9, 3)
        g = act(t, T_B[0] + 1.0, T_VS[0] + 0.4, 1.0, 0.7)
        if g > 0:
            gx, gy, gz = B['gpu']
            put('B', (gx, 6.6, 2.2), ['GPU: LOS MAS USADOS'], AMBERL, 0.8, g * 0.9, 2, sc(hexc('1A0608'), 1.0))
            put('B', (rx + 2.8, 6.4, -4.6), ['RAM: TODOS LOS DEMAS'], CYANL, 0.8, g * 0.9, 2,
                sc(hexc('1A0608'), 1.0))
            rt = B['router']
            put('B', tuple(rt + np.array([0, 2.0, 0])), ['ROUTER'], GOLDL, 0.75, g, 2)
            put('B', tuple(rt + np.array([0, 1.3, 0])), ['8 DE 24.576'], GOLDL, 0.85, g * 0.95, 2)
            put('B', (rx - 3.0, 1.8, 5.6), ['SSD: TABLA DE CONSULTA'], ICEL, 0.75, g * 0.8, 2)

    # ---- comparativa
    if t >= T_VS[0] - 0.3:
        f = act(t, T_VS[0] + 0.3, T_END[0] + 0.4, 0.9, 0.7)
        if f > 0:
            put('V', (-9.6, 8.8, 2.2), ['CAPAS'], ICEL, 1.2, f, 3)
            put('V', (-9.6, 7.9, 2.2), ['PESOS VIAJANDO'], REDL, 0.8, f * 0.9, 2)
            put('V', (9.6, 8.8, 2.2), ['EXPERTOS'], HOTL, 1.2, f, 3)
            put('V', (9.6, 7.9, 2.2), ['SOLO 8 POR TOKEN'], GOLDL, 0.8, f * 0.9, 2)
        g = act(t, T_VS[0] + 3.0, T_END[0] + 0.4, 1.4, 0.7)
        if g > 0:
            put('V', (0.0, 10.8, 3.2), ['MISMO PC: RTX 5070 12 GB + 64 GB RAM'], HOTL, 1.0, g, 3, PN)
            put('V', (-9.6, 6.6, 2.2), ['NO CABE EN 12 GB'], REDL, 0.9, g * 0.95, 2)
            put('V', (9.6, 6.6, 2.2), ['CABE  ·  53 TOKENS/S'], GOLDL, 0.9, g * 0.95, 2)

    # ---- cierre
    f = act(t, T_END[0] - 0.3, DUR, 1.2, 0.4)
    if f > 0:
        c = np.array([0.0, 6.6, 3.2])
        put('E', c, ['ANIMACION HECHA CON'], ICEL, 0.8, f * 0.8, 2)
        put('E', c - np.array([0, 1.3, 0]), ['QWEN 3.8 FLASH NEXT'], HOTL, 1.7, f, 4, PN)
        put('E', c - np.array([0, 2.9, 0]), ['CORRIENDO EN LOCAL CON STRATA'], GOLDL, 1.0,
            f * 0.9, 3)

    if no_bg:
        bgimg = None
    else:
        small = bgmod.background(t, max(320, W // 4), max(180, H // 4))
        bgimg = upscale_bilinear(small, W, H)
    return r.render(mesh, eye, tgt, fov, bg=bgimg)


if __name__ == '__main__':
    i = int(sys.argv[1]); W = int(sys.argv[2]); H = int(sys.argv[3])
    png_write(sys.argv[4], build_frame(i, W, H))
    print('ok', i)
