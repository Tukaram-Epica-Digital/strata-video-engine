import io
p = 'strata_video/raster.py'
s = io.open(p, encoding='utf-8').read()

old = """    def tex(self, arr):
        arr = np.asarray(arr, float)
        for i, t in enumerate(self.textures):
            if t.shape == arr.shape and np.array_equal(t, arr):
                return i
        self.textures.append(arr)
        return len(self.textures) - 1"""
new = """    def tex(self, arr, smooth=False):
        arr = np.asarray(arr, float)
        for i, t in enumerate(self.textures):
            if t.shape == arr.shape and np.array_equal(t, arr):
                return i
        self.textures.append(arr)
        if smooth:
            self.smooth.add(len(self.textures) - 1)
        return len(self.textures) - 1"""
assert old in s, 'tex block no encontrado'
s = s.replace(old, new)

old2 = "        self.textures = []\n"
assert old2 in s
s = s.replace(old2, "        self.textures = []\n        self.smooth = set()\n", 1)

# muestreado bilineal si la textura esta marcada
old3 = """                if img.ndim == 2:
                    th, tw = img.shape
                    px = np.clip(uu * (tw - 1), 0, tw - 1).astype(np.int32)
                    py = np.clip(vv * (th - 1), 0, th - 1).astype(np.int32)
                    s = img[py, px]"""
new3 = """                if img.ndim == 2:
                    th, tw = img.shape
                    if tid in self.smooth:
                        fx = uu * (tw - 1); fy = vv * (th - 1)
                        x0 = np.clip(np.floor(fx).astype(np.int32), 0, tw - 1)
                        y0 = np.clip(np.floor(fy).astype(np.int32), 0, th - 1)
                        x1 = np.minimum(x0 + 1, tw - 1); y1 = np.minimum(y0 + 1, th - 1)
                        wx = np.clip(fx - x0, 0, 1); wy = np.clip(fy - y0, 0, 1)
                        s = ((img[y0, x0] * (1 - wx) + img[y0, x1] * wx) * (1 - wy)
                             + (img[y1, x0] * (1 - wx) + img[y1, x1] * wx) * wy)
                    else:
                        px = np.clip(uu * (tw - 1), 0, tw - 1).astype(np.int32)
                        py = np.clip(vv * (th - 1), 0, th - 1).astype(np.int32)
                        s = img[py, px]"""
assert old3 in s, 'sampling block no encontrado'
s = s.replace(old3, new3)
io.open(p, 'w', encoding='utf-8').write(s)
print('ok: tex/smooth/bilinear aplicados')
