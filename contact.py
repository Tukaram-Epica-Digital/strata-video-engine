import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine import png_write
import scenes

TW, TH = 640, 360
frames = [45, 150, 300, 560, 760, 1000, 1200, 1400, 1620, 1700, 1760, 1830]
cols = 4
rows = (len(frames) + cols - 1) // cols
sheet = np.zeros((rows * TH, cols * TW, 3), np.float32)
for k, i in enumerate(frames):
    img = scenes.build_frame(i, TW, TH)
    r, c = divmod(k, cols)
    sheet[r * TH:(r + 1) * TH, c * TW:(c + 1) * TW] = img
    print(i, 'lum', round(float(img.mean()), 3), 'clip', round(float((img > 0.98).mean()), 4))
png_write('strata_video/contact.png', sheet)
print('sheet ok')
