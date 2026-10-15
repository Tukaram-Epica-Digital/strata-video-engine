"""Rotulos diegeticos: tamano en pixeles constante, autoajuste de ancho y
ancla siempre dentro del area segura del cuadro."""
import numpy as np
from engine import OPAQUE, ADD, sc, hexc
from font import text_alpha
from raster import TEX_SOFT

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


class Labels:
    """`frac` = altura del texto como fraccion de la ALTURA de pantalla."""
    SAFE = (0.055, 0.945, 0.075, 0.925)
    MAXW = 0.62          # ancho maximo como fraccion del ancho de pantalla

    def __init__(self, mesh, renderer, R, eye, target, fov, W, H):
        self.mesh = mesh
        self.r = renderer
        self.R = np.asarray(R, float)
        self.t = -self.R @ np.asarray(eye, float)
        self.eye = np.asarray(eye, float)
        self.W, self.H = int(W), int(H)
        self.focal = (self.W * 0.5) / np.tan(np.radians(fov) * 0.5)

    # ---- proyeccion
    def _to_screen(self, p):
        P = np.asarray(p, float) @ self.R.T + self.t
        z = max(float(P[2]), 0.3)
        return (P[0] / z * self.focal / self.W + 0.5,
                -P[1] / z * self.focal / self.H + 0.5, z)

    def _unproject(self, sx, sy, z):
        x = (sx - 0.5) * self.W * z / self.focal
        y = -(sy - 0.5) * self.H * z / self.focal
        return (np.array([x, y, z]) - self.t) @ self.R

    # ---- publico
    def at(self, pos, lines, color, frac=0.028, alpha=1.0, scale=3,
           panel=None, pad=0.55, anchor='c', emis=1.0, maxw=None):
        if alpha <= 0.01:
            return
        maxw = self.MAXW if maxw is None else maxw
        pos = np.asarray(pos, float)
        img = label_img(lines, scale)
        hp, wp = img.shape
        aspect = wp / hp
        s0, s1, y0, y1 = self.SAFE
        # 3 pasadas: mover el ancla cambia la distancia y por tanto el tamano
        for _ in range(3):
            sx, sy, z = self._to_screen(pos)
            px_h = frac * self.H                       # alto en pixeles
            px_w = px_h * aspect
            if px_w > maxw * self.W:                   # autoajuste por ancho
                k = (maxw * self.W) / px_w
                px_h *= k
                px_w *= k
            hw = 0.5 * px_w / self.W
            hh_s = 0.5 * px_h / self.H
            cx = float(np.clip(sx, s0 + hw, max(s0 + hw, s1 - hw)))
            cy = float(np.clip(sy, y0 + hh_s, max(y0 + hh_s, y1 - hh_s)))
            if abs(cx - sx) < 1e-4 and abs(cy - sy) < 1e-4:
                break
            pos = self._unproject(cx, cy, z)
        _, _, z = self._to_screen(pos)
        hh = px_h * z / self.focal
        ww = hh * aspect
        rx = self.R[0]
        if anchor == 'l':
            pos = pos + rx * (ww / 2)
        elif anchor == 'r':
            pos = pos - rx * (ww / 2)
        if panel is not None:
            self._q(pos - self.R[2] * 0.02, ww * (1 + pad * 0.4), hh * (1 + pad),
                    np.asarray(panel, float), alpha * 0.9, 1.0, TEX_SOFT)
        tid = self.r.tex(img, smooth=True)
        self._q(pos, ww, hh, np.asarray(color, float), alpha, emis, tid)

    def _q(self, p, w, h, color, alpha, emis, tex):
        r = self.R[0]; u = self.R[1]
        p = np.asarray(p, float)
        m = self.mesh
        m.quad(p - r * w / 2 - u * h / 2, p + r * w / 2 - u * h / 2,
               p + r * w / 2 + u * h / 2, p - r * w / 2 + u * h / 2,
               color, emis, 3, [alpha] * 4, tex, [[0, 0], [1, 0], [1, 1], [0, 1]])
