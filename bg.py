"""Fondo animado procedural en el estilo de FONDO.png del canal.
Base rojo profundo + resplandor ambar + filas de binario + glitchs cian.
Se renderiza a baja resolucion y se reescala (es barato y queda difuso a proposito).
"""
import numpy as np
from engine import hexc, sc

W0 = hexc('0E0306')
W1 = hexc('2A0705')
W2 = hexc('7A1A0C')
GLOW = hexc('FF9A2E')
HOTC = hexc('FFD08A')
GL_C = hexc('2E7FD8')
GL_C2 = hexc('6FD2FF')
GL_P = hexc('7A2E9E')

_cache = {}


def _digits(w, h, seed, cell=14):
    k = ('d', w, h, seed, cell)
    if k in _cache:
        return _cache[k]
    rng = np.random.default_rng(seed)
    cols = w // cell
    rows = h // cell
    canvas = np.zeros((h, w), float)
    glyphs = {
        '0': ['111', '1 1', '1 1', '1 1', '111'],
        '1': [' 1 ', '11 ', ' 1 ', ' 1 ', '111'],
    }
    for r in range(rows):
        y = r * cell + 2
        for c in range(cols):
            if rng.random() > 0.62:
                continue
            g = glyphs['0' if rng.random() < 0.5 else '1']
            for gy, row in enumerate(g):
                for gx, v in enumerate(row):
                    if v == '1' and y + gy < h and c * cell + gx * 2 + 3 < w:
                        canvas[y + gy, c * cell + gx * 2 + 3] = 1.0
    _cache[k] = canvas
    return canvas


def _streaks(w, h, seed, n=90):
    k = ('s', w, h, seed, n)
    if k in _cache:
        return _cache[k]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        y = int(rng.integers(0, h))
        x = int(rng.integers(-w * 0.2, w * 0.95))
        L = int(rng.integers(6, max(8, int(w * 0.16))))
        th = int(rng.integers(1, 4))
        kind = rng.random()
        col = GL_C2 if kind < 0.30 else (GL_C if kind < 0.55 else (GL_P if kind < 0.62 else None))
        a = float(rng.uniform(0.25, 1.0))
        out.append((x, y, L, th, col, a, float(rng.uniform(0.2, 1.6))))
    _cache[k] = out
    return out


def background(t, w, h, seed=3, intensity=1.0, glow_center=(0.52, 0.34)):
    """Devuelve (h,w,3) float lineal."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xx / w
    v = yy / h
    # base vertical: rojo profundo arriba -> mas negro abajo
    base = (1 - v) ** 1.35
    img = W0[None, None, :] * (1 - base[..., None]) + W1[None, None, :] * base[..., None]
    img += W2[None, None, :] * (np.clip(1 - np.abs(v - 0.42) * 2.4, 0, 1) ** 2)[..., None] * 0.35
    # resplandor calido principal (late ligeramente)
    pulse = 1.0 + 0.05 * np.sin(t * 0.9) + 0.03 * np.sin(t * 2.3 + 1.1)
    gx, gy = glow_center
    d = np.hypot((u - gx) / 0.55, (v - gy) / 0.48)
    g = np.clip(1 - d, 0, 1) ** 2.1 * pulse
    img = img * (1 + g[..., None] * 0.35) + GLOW[None, None, :] * g[..., None] * 0.62
    d2 = np.hypot((u - gx) / 0.22, (v - gy) / 0.18)
    g2 = np.clip(1 - d2, 0, 1) ** 2.4
    img += HOTC[None, None, :] * g2[..., None] * 0.30
    # vigneta lateral
    img *= (1 - 0.55 * np.clip((np.abs(u - 0.5) - 0.22) * 2.2, 0, 1) ** 1.6)[..., None]
    # filas de binario (derivan lentamente)
    dw, dh = max(160, w // 6), max(90, h // 6)
    off = int((t * 7) % 14)
    dig = _digits(dw, dh, seed)[(off):][:dh - off]
    dig = np.pad(dig, ((0, dh - dig.shape[0]), (0, 0)))[:dh, :dw]
    yi = np.linspace(0, dh - 1, h).astype(np.int32)
    xi = np.linspace(0, dw - 1, w).astype(np.int32)
    dm = dig[yi[:, None], xi[None, :]]
    fade = np.clip(1 - np.abs(v - gy) * 1.5, 0, 1)
    img += (0.10 + 0.22 * fade)[..., None] * dm[..., None] * np.array([1.0, 0.42, 0.16])[None, None, :]
    # glitchs horizontales
    for (sx, sy, L, th, col, a, sp) in _streaks(dw, dh, seed):
        px = int(((sx + t * 26 * sp) % (dw + 60)) / dw * w)
        py = int(sy / dh * h)
        ln = int(L / dw * w)
        hh = max(1, int(th / dh * h))
        sl = img[max(0, py):min(h, py + hh), max(0, px):min(w, px + ln)]
        if sl.size == 0:
            continue
        c = GL_C2 if col is None else col
        sl[:] = sl * 0.35 + np.asarray(c, float)[None, None, :] * a * 0.9
    return np.clip(img, 0, 1) * intensity
