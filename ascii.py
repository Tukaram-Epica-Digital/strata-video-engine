"""Ver composiciones en ASCII (para inspeccion sin poder ver imagenes)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes

CH = ' .:-=+*#%@'
RAMP = np.array([[0, 0, 0], [0.1, 0.05, 0.05], [0.2, 0.1, 0.05], [0.4, 0.2, 0.05],
                 [0.6, 0.35, 0.1], [0.8, 0.5, 0.15], [1.0, 0.7, 0.2], [1.0, 0.85, 0.4],
                 [1.0, 0.95, 0.7], [1.0, 1.0, 1.0]])


def show(i, W=480, H=270, cols=80, rows=36):
    img = scenes.build_frame(i, W, H)
    h, w = img.shape[:2]
    ys = np.linspace(0, h - 1, rows).astype(int)
    xs = np.linspace(0, w - 1, cols).astype(int)
    s = img[ys[:, None], xs[None, :], :]
    L = (0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2])
    out = []
    for r in range(rows):
        line = ''
        for c in range(cols):
            v = float(np.clip(L[r, c] * 1.6, 0, 0.999))
            line += CH[int(v * len(CH))]
        out.append(line)
    print('=== frame %d  t=%.2f ===' % (i, i / scenes.FPS))
    print('\n'.join(out))


if __name__ == '__main__':
    for a in sys.argv[1:]:
        show(int(a))
