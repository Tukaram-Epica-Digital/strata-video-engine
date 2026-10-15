import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine import png_write
import scenes

for i in [int(x) for x in sys.argv[1:]]:
    t0 = time.time()
    img = scenes.build_frame(i, 1280, 720)
    png_write('strata_video/preview/f%05d.png' % i, img)
    print('frame', i, round(time.time() - t0, 2), 's')
