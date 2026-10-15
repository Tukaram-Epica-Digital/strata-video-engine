"""ASCII codificado por color dominante: permite 'ver' que objeto esta donde."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes

# simbolos por familia de color
RULES = [
    ('#', lambda r, g, b: r > 0.55 and g > 0.45 and b > 0.30),      # blanco/calido (tokens, textos)
    ('A', lambda r, g, b: r > 0.45 and g > 0.18 and b < 0.25),      # ambar/naranja (GPU)
    ('C', lambda r, g, b: b > 0.30 and b > r * 0.9),                # cian (RAM/CPU)
    ('R', lambda r, g, b: r > 0.30 and g < 0.14 and b < 0.16),      # rojo (PCIe)
    ('G', lambda r, g, b: g > 0.12 and g > r * 0.9),                # verde (PCB)
    ('.', lambda r, g, b: True),
]


def colmap(i, W=480, H=270, cols=92, rows=42):
    img = scenes.build_frame(i, W, H, no_bg=True)
    h, w = img.shape[:2]
    ys = np.linspace(0, h - 1, rows).astype(int)
    xs = np.linspace(0, w - 1, cols).astype(int)
    s = img[ys[:, None], xs[None, :], :]
    print('=== frame %d t=%.2f ===  A=GPU  C=RAM/CPU  R=PCIe  #=luz/texto  .=tenue'
          % (i, i / scenes.FPS))
    for r in range(rows):
        line = ''
        for c in range(cols):
            R_, G_, B_ = float(s[r, c, 0]), float(s[r, c, 1]), float(s[r, c, 2])
            L = 0.2126 * R_ + 0.7152 * G_ + 0.0722 * B_
            if L < 0.035:
                line += ' '
                continue
            for sym, f in RULES:
                if f(R_, G_, B_):
                    line += sym
                    break
        print(line)


if __name__ == '__main__':
    for a in sys.argv[1:]:
        colmap(int(a))
