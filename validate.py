"""Validacion: en cada frame, la geometria y los rotulos deben caer dentro del area segura."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes
from framing import project
from engine import look_at

W, H = 960, 540
SAFE = scenes.SAFE


def check(i, verbose=False):
    t = i / scenes.FPS
    ang, el, fov = scenes.orbit(t)
    u = np.array([np.sin(ang) * np.cos(el), np.sin(el), np.cos(ang) * np.cos(el)])
    # reproducir construccion
    from raster import Renderer
    from props import motherboard
    r = Renderer(W, H)
    mesh = scenes.Mesh()
    info = {}
    bbs = []
    if t < scenes.T_VS[0]:
        if t > scenes.T_A[0] - 0.6 and t < scenes.T_TRANS[0] + 0.8:
            info['A'] = scenes.scene_A(mesh, r, t); bbs.append(info['A']['bb'])
        if t > scenes.T_TRANS[0] - 0.4 and t < scenes.T_VS[0] + 0.8:
            info['B'] = scenes.scene_B(mesh, r, t); bbs.append(info['B']['bb'])
    else:
        info['A'] = scenes.scene_A(mesh, r, t, off=(-9.6, 0, 0), s=0.60)
        info['B'] = scenes.scene_B(mesh, r, t, off=(9.6, 0, 0), s=0.60)
        bbs = [scenes.merge_bb(info['A']['bb'], info['B']['bb'])]
    if not bbs:
        bbs = [(-11.6, 12.6, 0.0, 6.2, -5.8, 2.6)]
    bb = bbs[0]
    for b in bbs[1:]:
        bb = scenes.merge_bb(bb, b)
    pts = scenes.corners(bb)
    center = np.array([(bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2 * 0.85, (bb[4] + bb[5]) / 2])
    from framing import fit_view
    eye, tgt = fit_view(pts, center, u, fov, W, H, SAFE, dmin=4.0, dmax=70.0)
    sx, sy, z = project(pts, eye, tgt, fov, W, H)
    geo_ok = (z > 0.2).all() and sx.min() > SAFE[0] - 1e-6 and sx.max() < SAFE[1] + 1e-6 \
        and sy.min() > SAFE[2] - 1e-6 and sy.max() < SAFE[3] + 1e-6
    dist = float(np.linalg.norm(eye - center))
    if verbose:
        print('f%05d t=%5.2f cam_d=%6.2f geo x[%.3f,%.3f] y[%.3f,%.3f] %s'
              % (i, t, dist, sx.min(), sx.max(), sy.min(), sy.max(), 'OK' if geo_ok else 'FUERA'))
    return geo_ok, dist


if __name__ == '__main__':
    bad = 0
    step = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    verb = '-v' in sys.argv
    for i in range(0, scenes.NF, step):
        ok, d = check(i, verb)
        if not ok:
            bad += 1
            check(i, True)
    print('frames comprobados:', len(range(0, scenes.NF, step)), 'con problema de encuadre:', bad)
