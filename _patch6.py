import io
p = 'strata_video/raster.py'
s = io.open(p, encoding='utf-8').read()

# 1) registro de texturas con muestreado suave
s = s.replace("""    def tex(self, arr):
        arr = np.asarray(arr, float)
        for i, t in enumerate(self.textures):
            if t.shape == arr.shape and np.array_equal(t, arr):
                return i
        self.textures.append(arr)
        return len(self.textures) - 1""",
"""    def tex(self, arr, smooth=False):
        arr = np.asarray(arr, float)
        for i, t in enumerate(self.textures):
            if t.shape == arr.shape and np.array_equal(t, arr):
                return i
        self.textures.append(arr)
        if smooth:
            self.smooth.add(len(self.textures) - 1)
        return len(self.textures) - 1""")
s = s.replace("        self.textures = []\n        self.special",
              "        self.textures = []\n        self.smooth = set()\n        self.special")

# 2) muestreado bilineal para texturas suaves (texto antialiased)
old = """                if img.ndim == 2:
                    th, tw = img.shape
                    px = np.clip(uu * (tw - 1), 0, tw - 1).astype(np.int32)
                    py = np.clip(vv * (th - 1), 0, th - 1).astype(np.int32)
                    s = img[py, px]
                    c = base[None, :] * s[:, None]
                else:
                    th, tw = img.shape[:2]
                    px = np.clip(uu * (tw - 1), 0, tw - 1).astype(np.int32)
                    py = np.clip(vv * (th - 1), 0, th - 1).astype(np.int32)
                    c = img[py, px] * base[None, :]
                al = (b0 * VA[ti][0] + b1 * VA[ti][1] + b2 * VA[ti][2])
                if img.ndim == 2:
                    al = al * s"""
new = """                smooth = (tid in self.smooth)
                if img.ndim == 2:
                    th, tw = img.shape
                    if smooth:
                        fx = uu * (tw - 1); fy = vv * (th - 1)
                        x0 = np.clip(np.floor(fx).astype(np.int32), 0, tw - 1)
                        y0 = np.clip(np.floor(fy).astype(np.int32), 0, th - 1)
                        x1 = np.minimum(x0 + 1, tw - 1); y1 = np.minimum(y0 + 1, th - 1)
                        wx = np.clip(fx - x0, 0, 1); wy = np.clip(fy - y0, 0, 1)
                        s = (img[y0, x0] * (1 - wx) + img[y0, x1] * wx) * (1 - wy) \\
                            + (img[y1, x0] * (1 - wx) + img[y1, x1] * wx) * wy
                    else:
                        px = np.clip(uu * (tw - 1), 0, tw - 1).astype(np.int32)
                        py = np.clip(vv * (th - 1), 0, th - 1).astype(np.int32)
                        s = img[py, px]
                    c = base[None, :] * s[:, None]
                else:
                    th, tw = img.shape[:2]
                    px = np.clip(uu * (tw - 1), 0, tw - 1).astype(np.int32)
                    py = np.clip(vv * (th - 1), 0, th - 1).astype(np.int32)
                    c = img[py, px] * base[None, :]
                    s = img[py, px].mean(axis=1)
                al = (b0 * VA[ti][0] + b1 * VA[ti][1] + b2 * VA[ti][2]) * s"""
assert old in s
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('raster ok')
