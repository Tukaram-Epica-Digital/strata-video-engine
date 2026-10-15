import time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine import Mesh, radial, OPAQUE, ADD, AMBER, CYAN, STEEL, sc
from raster import Renderer

W, H, SS = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
NT = int(sys.argv[4]) if len(sys.argv) > 4 else 2000

m = Mesh()
rng = np.random.default_rng(0)
for i in range(NT):
    p = np.array([rng.uniform(-4, 4), rng.uniform(0, 3), rng.uniform(-4, 4)])
    m.box(p, [0.2, 0.2, 0.2], STEEL, 0.0)
    m.wire(p, [0.22, 0.22, 0.22], AMBER, 0.012)
r = Renderer(W, H, ss=SS, lights=[{'dir': (-0.4, -1, -0.3), 'int': 1.2, 'col': np.ones(3)}],
             bloom=0.8, vignette=0.25)
t0 = time.time()
img, R = r.render(m.finish(), [-7, 4, 9], [0, 1, 0], 45)
dt = time.time() - t0
print('tris', len(m.T), 'res', W * SS, H * SS, 'frame', round(dt, 2), 's')
print('est 1500 frames 1 proceso:', round(dt * 1500 / 60, 1), 'min')
