import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scenes

i = int(sys.argv[1])
img = scenes.build_frame(i, 480, 270, no_bg=True)
flat = img.reshape(-1, 3)
L = 0.2126 * flat[:, 0] + 0.7152 * flat[:, 1] + 0.0722 * flat[:, 2]
print('pixeles', flat.shape[0])
for lo, hi in [(0, 0.02), (0.02, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.4), (0.4, 1.0)]:
    m = (L >= lo) & (L < hi)
    if m.sum() == 0:
        continue
    print('lum %.2f-%.2f  %6.1f%%  color medio %s' %
          (lo, hi, 100 * m.mean(), np.round(flat[m].mean(axis=0), 3)))
