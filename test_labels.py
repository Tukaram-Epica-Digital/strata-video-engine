"""Prueba aislada de rotulos: fuente, tamano y legibilidad."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine import Mesh, look_at, sc, hexc, png_write
from raster import Renderer
from props import label3d, AMBERL, GOLDL, HOTL, ICEL

W, H = 960, 540
eye = np.array([0.0, 3.0, 12.0]); tgt = np.array([0.0, 3.0, 0.0])
R, _ = look_at(eye, tgt)
mesh = Mesh()
r = Renderer(W, H, ambient=0.0, rim=0.0, bloom=0.6, bloom_thr=0.4, vignette=0.0, grain=0.0)
cases = [
    ((-4.0, 5.0, 0.0), ['PRUEBA DE TEXTO'], HOTL, 0.9, 4),
    ((-4.0, 3.6, 0.0), ['CON FONDO DETRAS'], GOLDL, 0.6, 3),
    ((-4.0, 2.4, 0.0), ['GPU 12 GB  ·  24.576'], ICEL, 0.4, 2),
    ((4.0, 3.6, 0.0), ['CON PANEL'], AMBERL, 0.6, 3),
]
for pos, lines, col, hgt, sc_ in cases:
    kw = {}
    if 'PANEL' in lines[0]:
        kw['panel'] = sc(hexc('1A0408'), 1.0)
    label3d(mesh, r, R, pos, lines, col, height=hgt, alpha=1.0, scale=sc_, **kw)
img = r.render(mesh, eye, tgt, 45, bg=np.zeros((H, W, 3), np.float32))
png_write('strata_video/preview/labels.png', img)
L = 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]
print('lum max', round(float(L.max()), 3), 'pix brillantes', int((L > 0.5).sum()))
CH = ' .:-=+*#%@'
ys = np.linspace(0, H - 1, 34).astype(int); xs = np.linspace(0, W - 1, 90).astype(int)
s = L[ys[:, None], xs[None, :]]
for rr in range(34):
    print(''.join(CH[int(np.clip(s[rr, cc], 0, 0.999) * 10)] for cc in range(90)))
