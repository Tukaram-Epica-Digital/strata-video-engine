"""Aislamiento: geometria sola (fondo negro) en ASCII, para validar composicion."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes

CH = ' .:-=+*#%@'


def geo(i, W=480, H=270, cols=88, rows=40):
    img = scenes.build_frame(i, W, H, no_bg=True)
    h, w = img.shape[:2]
    ys = np.linspace(0, h - 1, rows).astype(int)
    xs = np.linspace(0, w - 1, cols).astype(int)
    s = img[ys[:, None], xs[None, :], :]
    L = (0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2])
    print('=== GEOMETRIA frame %d t=%.2f  (max %.2f) ===' % (i, i / scenes.FPS, L.max()))
    for r in range(rows):
        print(''.join(CH[int(np.clip(L[r, c], 0, 0.999) * len(CH))] for c in range(cols)))


if __name__ == '__main__':
    for a in sys.argv[1:]:
        geo(int(a))
