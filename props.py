"""Piezas del diorama 3D: placa, GPU, CPU, RAM, SSD, etiquetas flotantes."""
import numpy as np
from engine import (Mesh, OPAQUE, ADD, norm, sc, hexc, radial, board_grid, soft_rect)
from raster import TEX_GLOW, TEX_DOT, TEX_SOFT
from font import text_alpha

AMBERL = hexc('FF8A1E')
GOLDL = hexc('FFC24A')
HOTL = hexc('FFEBC2')
REDL = hexc('E8342B')
DIML = hexc('5A1A16')
CYANL = hexc('3FA8FF')
ICEL = hexc('A8E8FF')
GRN = hexc('2FBF7A')

_lc = {}


def label_img(lines, scale=3, tracking=1, gap=2):
    key = (tuple(lines), scale, tracking, gap)
    if key in _lc:
        return _lc[key]
    if isinstance(lines, str):
        lines = [lines]
    imgs = [text_alpha(l, 1, tracking) for l in lines]
    w = max(i.shape[1] for i in imgs)
    h = len(imgs) * 7 + (len(imgs) - 1) * gap
    out = np.zeros((h, w))
    y = 0
    for i in imgs:
        pad = (w - i.shape[1]) // 2
        out[y:y + 7, pad:pad + i.shape[1]] = i
        y += 7 + gap
    out = np.repeat(np.repeat(out, scale, 0), scale, 1)
    _lc[key] = out
    return out


def _quad_bb(mesh, R, p, w, h, color, alpha, emis, tex):
    if R is None:
        r = np.array([1.0, 0, 0]); u = np.array([0, 1.0, 0])
    else:
        r = np.asarray(R, float)[0]; u = np.asarray(R, float)[1]
    p = np.asarray(p, float)
    a = p - r * w / 2 - u * h / 2
    b = p + r * w / 2 - u * h / 2
    c = p + r * w / 2 + u * h / 2
    d = p - r * w / 2 + u * h / 2
    mesh.quad(a, b, c, d, color, emis, ADD, [alpha] * 4, tex,
              [[0, 0], [1, 0], [1, 1], [0, 1]])


def label3d(mesh, renderer, R, pos, lines, color, height=0.5, alpha=1.0,
            scale=3, emis=1.0, anchor='c', panel=None, pad=0.55):
    """texto orientado a camara dentro de la escena 3D (diegetico)"""
    img = label_img(lines, scale)
    hp, wp = img.shape
    hh = float(height)
    ww = hh * wp / hp
    p = np.asarray(pos, float)
    r = np.asarray(R, float)[0]
    if anchor == 'l':
        p = p + r * (ww / 2)
    elif anchor == 'r':
        p = p - r * (ww / 2)
    if panel is not None:
        _quad_bb(mesh, R, p - np.asarray(R, float)[2] * 0.05, ww * (1 + pad * 0.35),
                 hh * (1 + pad), np.asarray(panel, float), alpha * 0.85, 1.0, TEX_SOFT)
    tid = renderer.tex(img)
    _quad_bb(mesh, R, p, ww, hh, np.asarray(color, float), alpha, emis, tid)


def motherboard(mesh, renderer):
    # placa oscura: insinua el hardware, no domina el cuadro
    tid = renderer.tex(board_grid(512, 26, 0.055, 0.006))
    mesh.quad(np.array([-13, 0, -9]), np.array([13, 0, -9]), np.array([13, 0, 7]),
              np.array([-13, 0, 7]), hexc('120709'), 0.0, OPAQUE, 1.0, tid,
              [[0, 0], [1, 0], [1, 1], [0, 1]])
    for (x, z, sx, sz) in [(-13, -1, 0.14, 16), (13, -1, 0.14, 16), (0, -9, 26, 0.14), (0, 7, 26, 0.14)]:
        mesh.box((x, 0.07, z), (sx, 0.14, sz), hexc('2A1712'), 0.0)
    rng = np.random.default_rng(4)
    for _ in range(18):
        x = rng.uniform(-12, 12); z = rng.uniform(-8, 6)
        L = rng.uniform(0.6, 3.2); hz = rng.random() < 0.5
        p0 = np.array([x, 0.03, z])
        p1 = np.array([x + (L if hz else 0), 0.03, z + (0 if hz else L)])
        mesh.bar(p0, p1, 0.035, hexc('6B3A22'), 0.02, OPAQUE)


def gpu_card(mesh, renderer, pos, t, w=7.2, d=3.2, load=0.0):
    x, y, z = pos
    mesh.box((x, y, z), (w, 0.16, d), hexc('0F2A1C'), 0.0)
    mesh.wire((x, y, z), (w, 0.16, d), sc(GRN, 0.30), 0.02)
    mesh.box((x, y + 0.22, z), (w * 0.95, 0.28, d * 0.93), hexc('17171C'), 0.0)
    mesh.box((x, y + 0.40, z), (w * 0.90, 0.10, d * 0.86), hexc('24242B'), 0.0)
    for fx in (x - w * 0.27, x + w * 0.27):
        rr = d * 0.36
        for k in range(9):
            a = t * 3.4 + k * 2 * np.pi / 9
            p0 = np.array([fx + np.cos(a) * rr * 0.16, y + 0.47, z + np.sin(a) * rr * 0.16])
            p1 = np.array([fx + np.cos(a) * rr * 0.94, y + 0.47, z + np.sin(a) * rr * 0.94])
            mesh.bar(p0, p1, 0.10, hexc('2C2C34'), 0.04, OPAQUE)
        _quad_bb(mesh, np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]]),
                 (fx, y + 0.48, z), rr * 0.45, rr * 0.45, hexc('3A3A46'), 1.0, 0.15, TEX_DOT)
    mesh.box((x - w * 0.16, y - 0.18, z), (w * 0.52, 0.18, d * 0.18), hexc('B9862A'), 0.10)
    _quad_bb(mesh, None, (x + w * 0.47, y + 0.34, z), 0.30 + 0.10 * np.sin(t * 9),
             0.30 + 0.10 * np.sin(t * 9), sc(AMBERL, 0.5 + load), 0.5 + load, 1.0, TEX_GLOW)


def panel_z(mesh, pos, w, h, tex, alpha=1.0, frame=GOLDL):
    p = np.asarray(pos, float)
    mesh.quad(p + [-w / 2, -h / 2, 0], p + [w / 2, -h / 2, 0], p + [w / 2, h / 2, 0],
              p + [-w / 2, h / 2, 0], np.ones(3), 1.0, OPAQUE, [alpha] * 4, tex,
              [[0, 0], [1, 0], [1, 1], [0, 1]])
    mesh.wire(p, (w, h, 0.02), sc(frame, 0.55), 0.02)


def cpu_block(mesh, pos, t, glow=0.6):
    x, y, z = pos
    mesh.box((x, y - 0.12, z), (2.6, 0.24, 2.6), hexc('16283A'), 0.0)
    mesh.box((x, y + 0.05, z), (1.9, 0.16, 1.9), hexc('7E878F'), 0.04)
    mesh.wire((x, y + 0.05, z), (1.94, 0.18, 1.94), sc(CYANL, glow), 0.03)
    for k in range(5):
        xx = x - 0.8 + k * 0.4
        mesh.box((xx, y + 0.34, z), (0.10, 0.55, 1.8), hexc('2A2E33'), 0.0)
    _quad_bb(mesh, None, (x, y + 0.14, z), 1.1, 1.1, sc(CYANL, glow), glow * 0.8, 1.0, TEX_GLOW)


def ram_sticks(mesh, x0, z, n=4, glow=0.0, gap=0.75, h=2.6):
    for i in range(n):
        x = x0 + i * gap
        mesh.box((x, 0.12, z), (0.16, 0.24, 3.2), hexc('0F2A1C'), 0.0)
        mesh.box((x, 1.15, z), (0.18, h, 3.1), hexc('141419'), 0.0)
        for k in range(7):
            zz = z - 1.3 + k * 0.44
            mesh.box((x, 1.15, zz), (0.22, 0.36, 0.34), hexc('0A0A0E'), 0.0)
        mesh.wire((x, 1.15, z), (0.22, h, 3.14), sc(AMBERL, 0.15 + glow * 0.7), 0.02)


def ssd_drive(mesh, x0, z, glow=0.0, L=7.0):
    xc = x0 + L / 2
    mesh.box((xc, 0.10, z), (L, 0.16, 1.1), hexc('0E1620'), 0.0)
    mesh.wire((xc, 0.10, z), (L, 0.16, 1.1), sc(GOLDL, 0.18 + glow * 0.6), 0.02)
    for k in range(4):
        xx = x0 + 0.6 + k * (L - 1.4) / 3
        mesh.box((xx, 0.20, z), (0.8, 0.12, 0.7), hexc('090910'), 0.0)


def token3d(mesh, pos, color, size=0.22, glow=1.0):
    p = np.asarray(pos, float); s = float(size)
    top = p + [0, s, 0]; bot = p - [0, s, 0]
    ring = [p + [s, 0, 0], p + [0, 0, s], p + [-s, 0, 0], p + [0, 0, -s]]
    for i in range(4):
        a = ring[i]; b = ring[(i + 1) % 4]
        mesh.tri(a, b, top, color, 1.0, ADD)
        mesh.tri(b, a, bot, color, 1.0, ADD)
    _quad_bb(mesh, None, p, size * 4.2, size * 4.2, color, glow * 0.85, 1.0, TEX_GLOW)


def glow_quad(mesh, pos, w, h, color, alpha, R=None):
    _quad_bb(mesh, R, pos, w, h, color, alpha, 1.0, TEX_GLOW)


def gauge3d(mesh, pos, w, h, frac, col_fill, col_frame):
    x, y, z = pos
    mesh.box((x, y, z), (w, h, 0.10), hexc('1A0A0C'), 0.0)
    mesh.wire((x, y, z), (w, h, 0.10), sc(col_frame, 0.9), 0.02)
    fw = w * float(np.clip(frac, 0, 1))
    if fw > 0.02:
        mesh.box((x - w / 2 + fw / 2, y, z + 0.07), (fw, h * 0.7, 0.06), col_fill, 1.0)
