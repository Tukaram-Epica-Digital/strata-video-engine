import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes
from engine import look_at, Mesh

i = int(sys.argv[1]) if len(sys.argv) > 1 else 300
t = i / scenes.FPS
eye, tgt, fov = scenes.cam_for(t)
print('eye', np.round(eye, 2), 'tgt', np.round(tgt, 2), 'fov', fov)

# reproducir construccion sin render
from raster import Renderer
from props import motherboard
r = Renderer(960, 540)
mesh = Mesh()
motherboard(mesh, r)
if t >= scenes.T_A[0] - 0.5:
    scenes.scene_A(mesh, r, t)
m = mesh.finish()
print('verts', m['V'].shape, 'tris', m['T'].shape)
R, tt = look_at(eye, tgt)
P = m['V'] @ R.T + tt
print('cam-space z: min %.2f max %.2f' % (P[:, 2].min(), P[:, 2].max()))
good = P[:, 2] > 0.05
focal = (960 * 0.5) / np.tan(np.radians(fov) * 0.5)
SX = P[:, 0] / np.maximum(P[:, 2], 1e-9) * focal + 480
SY = -P[:, 1] / np.maximum(P[:, 2], 1e-9) * focal + 270
g = good
print('sx range %.1f %.1f  sy range %.1f %.1f' % (SX[g].min(), SX[g].max(), SY[g].min(), SY[g].max()))
inside = ((SX[g] > 0) & (SX[g] < 960) & (SY[g] > 0) & (SY[g] < 540)).mean()
print('verts inside frame: %.3f' % inside)
