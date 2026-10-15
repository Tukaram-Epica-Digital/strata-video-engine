"""Comprueba que los quads de rotulo (blend=3 con textura) caen dentro del area segura."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes
from raster import Renderer
from engine import look_at

W, H = 960, 540


def scan(i):
    t = i / scenes.FPS
    ang, el, fov = scenes.orbit(t)
    # reproducir el frame completo capturando la malla
    import scenes as S
    orig = S.Renderer
    holder = {}

    # monkeypatch: interceptar el render para coger la malla
    def patched(*a, **k):
        return np.zeros((H, W, 3))
    import raster
    real = raster.Renderer.render
    def cap(self, mesh, eye, target, fovi, up=(0, 1, 0), bg=None):
        holder['mesh'] = mesh
        holder['eye'] = eye; holder['tgt'] = target; holder['fov'] = fovi
        return real(self, mesh, eye, target, fov, up, bg)
    raster.Renderer.render = cap
    try:
        S.build_frame(i, W, H, no_bg=True)
    finally:
        raster.Renderer.render = real
    m = holder['mesh'].finish() if hasattr(holder['mesh'], 'finish') else holder['mesh']
    eye = holder['eye']; tgt = holder['tgt']; fov = holder['fov']
    R, tt = look_at(eye, tgt)
    V = m['V']; T = m['T']; BL = m['BL']; TEX = m['TEX']
    P = V @ R.T + tt
    z = np.maximum(P[:, 2], 1e-6)
    focal = (W * 0.5) / np.tan(np.radians(fov) * 0.5)
    sx = P[:, 0] / z * focal / W + 0.5
    sy = -P[:, 1] / z * focal / H + 0.5
    bad = 0
    n = 0
    for ti in range(len(T)):
        if BL[ti] != 3 or TEX[ti] < 0:
            continue
        n += 1
        a, b, c = T[ti]
        pts = [(sx[a], sy[a]), (sx[b], sy[b]), (sx[c], sy[c])]
        # el quad se compone de 2 triangulos; basta con este
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if min(xs) < 0.02 or max(xs) > 0.98 or min(ys) < 0.02 or max(ys) > 0.98:
            bad += 1
    print('f%05d t=%5.2f  rotulos=%d  fuera=%d' % (i, t, n, bad))
    return bad


if __name__ == '__main__':
    tot = 0
    for a in sys.argv[1:]:
        tot += scan(int(a))
    print('total fuera de cuadro:', tot)
