import io
p = 'strata_video/labels.py'
s = io.open(p, encoding='utf-8').read()
old = """        pos = np.asarray(pos, float)
        sx, sy, z = self._to_screen(pos)
        img = label_img(lines, scale)
        hp, wp = img.shape
        # tamano en unidades de pantalla (constante en pixeles)
        hh = self.k * z * float(frac)
        ww = hh * wp / hp
        hw = 0.5 * ww * self.focal / self.W / max(z, 0.3) * z
        hh_s = 0.5 * hh * self.focal / self.H * (self.H / self.H)
        hw = 0.5 * (ww * self.focal / max(z, 0.3)) / self.W
        hh_s = 0.5 * (hh * self.focal / max(z, 0.3)) / self.H
        s0, s1, y0, y1 = self.SAFE
        cx = float(np.clip(sx, s0 + hw, s1 - hw))
        cy = float(np.clip(sy, y0 + hh_s, y1 - hh_s))
        if (cx, cy) != (sx, sy):
            pos = self._unproject(cx, cy, z)
        dist = float(np.linalg.norm(pos - self.eye))
        hh = self.k * dist * float(frac)
        ww = hh * wp / hp
        rx = self.R[0]"""
new = """        pos = np.asarray(pos, float)
        img = label_img(lines, scale)
        hp, wp = img.shape
        s0, s1, y0, y1 = self.SAFE
        # dos pasadas: al mover el ancla cambia la distancia y por tanto el tamano
        for _ in range(2):
            sx, sy, z = self._to_screen(pos)
            hh = self.k * z * float(frac)
            ww = hh * wp / hp
            hw = 0.5 * (ww * self.focal / max(z, 0.3)) / self.W
            hh_s = 0.5 * (hh * self.focal / max(z, 0.3)) / self.H
            cx = float(np.clip(sx, s0 + hw, s1 - hw))
            cy = float(np.clip(sy, y0 + hh_s, y1 - hh_s))
            if (cx, cy) != (sx, sy):
                pos = self._unproject(cx, cy, z)
        dist = float(np.linalg.norm(pos - self.eye))
        hh = self.k * dist * float(frac)
        ww = hh * wp / hp
        rx = self.R[0]"""
assert old in s
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('clamp iterativo ok')
