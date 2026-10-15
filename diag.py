"""Diagnosticos numericos: contraste geometria/fondo, legibilidad, recortes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes
import bg as bgmod
from raster import upscale_bilinear


def lum(i):
    return (0.2126 * i[..., 0] + 0.7152 * i[..., 1] + 0.0722 * i[..., 2])


def analyse(i, W=960, H=540):
    t = i / scenes.FPS
    full = scenes.build_frame(i, W, H)
    # fondo solo
    small = bgmod.background(t, max(320, W // 4), max(180, H // 4))
    bgonly = upscale_bilinear(small, W, H)
    bgonly = np.power(np.clip(bgonly / (1 + bgonly), 0, 1) ** (1 / 2.2), 1)
    d = np.abs(lum(full) - lum(bgonly))
    vis = (d > 0.06).mean()
    strong = (d > 0.20).mean()
    L = lum(full)
    print('f%05d t=%5.2f  lum=%.3f  p05=%.3f p95=%.3f  clip=%.4f  visible=%.3f  fuerte=%.3f'
          % (i, t, L.mean(), np.percentile(L, 5), np.percentile(L, 95),
             (full > 0.985).mean(), vis, strong))
    return full


if __name__ == '__main__':
    for i in [int(x) for x in sys.argv[1:]]:
        analyse(i)
