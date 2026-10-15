"""Rasterizador con z-buffer por pintor + post (bloom, tonemap, vineta, grano)."""
import numpy as np
from engine import NEAR, norm, radial, soft_rect

# codigos de textura especial (negativos) -> texturas del propio renderer
TEX_GLOW = -5
TEX_DOT = -1
TEX_SOFT = -6


def _blur(a, r):
    if r < 1:
        return a
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / (r * 0.62)) ** 2)
    k /= k.sum()
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 1, a)
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 0, out)
    return out


def upscale_bilinear(img, W, H):
    h, w = img.shape[:2]
    if (h, w) == (H, W):
        return img
    xs = np.linspace(0, w - 1, W)
    ys = np.linspace(0, h - 1, H)
    x0 = np.floor(xs).astype(np.int32); x1 = np.minimum(x0 + 1, w - 1)
    y0 = np.floor(ys).astype(np.int32); y1 = np.minimum(y0 + 1, h - 1)
    fx = (xs - x0).astype(np.float32)[None, :, None]
    fy = (ys - y0).astype(np.float32)[:, None, None]
    a = img[y0][:, x0]
    b = img[y0][:, x1]
    c = img[y1][:, x0]
    d = img[y1][:, x1]
    return ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)


class Renderer:
    def __init__(self, W, H, ss=1, lights=None, ambient=0.20, rim=0.7,
                 exposure=1.0, bloom=0.8, bloom_thr=0.5, vignette=0.28,
                 grain=0.008, fog_col=None, fog_k=0.0):
        self.W, self.H, self.ss = int(W), int(H), int(ss)
        self.RW, self.HH = self.W * self.ss, self.H * self.ss
        self.lights = lights or []
        self.ambient = ambient; self.rim = rim
        self.exposure = exposure; self.bloom = bloom; self.bloom_thr = bloom_thr
        self.vignette = vignette; self.grain = grain
        self.fog_col = fog_col; self.fog_k = fog_k
        self.textures = []
        self.smooth = set()
        self.special = {TEX_GLOW: radial(128, 2.2), TEX_DOT: radial(64, 1.6),
                        TEX_SOFT: soft_rect(64, 64, 0.22)}

    def tex(self, arr, smooth=False):
        arr = np.asarray(arr, float)
        for i, t in enumerate(self.textures):
            if t.shape == arr.shape and np.array_equal(t, arr):
                return i
        self.textures.append(arr)
        if smooth:
            self.smooth.add(len(self.textures) - 1)
        return len(self.textures) - 1

    def render(self, mesh, eye, target, fov, up=(0, 1, 0), bg=None):
        from engine import look_at
        if hasattr(mesh, 'finish'):
            mesh = mesh.finish()
        R, t = look_at(eye, target, up)
        RW, HH = self.RW, self.HH
        focal = (RW * 0.5) / np.tan(np.radians(fov) * 0.5)
        col = np.zeros((HH, RW, 3), np.float32) if bg is None else np.ascontiguousarray(bg, np.float32)
        zbuf = np.full((HH, RW), np.inf, np.float32)

        V = mesh['V']
        if len(mesh['T']) == 0:
            return self._post(col)
        P = V @ R.T + t
        Wz = P[:, 2]
        inv = np.zeros_like(Wz)
        good = Wz > NEAR
        inv[good] = 1.0 / Wz[good]
        SX = (P[:, 0] * inv * focal + RW * 0.5).astype(np.float32)
        SY = (-P[:, 1] * inv * focal + HH * 0.5).astype(np.float32)

        T = mesh['T']
        a = V[T[:, 0]]; b = V[T[:, 1]]; c = V[T[:, 2]]
        N = np.cross(b - a, c - a)
        nl = np.linalg.norm(N, axis=1)
        N = np.where(nl[:, None] > 1e-12, N / np.maximum(nl[:, None], 1e-12), 0.0)
        COL = mesh['COL']; EM = mesh['EM']
        shade = COL * self.ambient
        for L in self.lights:
            ld = norm(np.asarray(L['dir'], float))
            nd = np.clip(N @ (-ld), 0, 1)
            shade += (COL * nd[:, None]) * float(L['int']) * np.asarray(L['col'], float)
        if self.rim > 0:
            ctr = (a + b + c) / 3.0
            vd = norm(ctr - np.asarray(eye, float))
            ff = np.clip(1.0 - np.abs(np.einsum('ij,ij->i', N, vd)), 0, 1) ** 3
            shade += COL * ff[:, None] * self.rim
        final = shade * (1.0 - EM[:, None]) + COL * EM[:, None]
        if self.fog_k > 0 and self.fog_col is not None:
            dep = (Wz[T[:, 0]] + Wz[T[:, 1]] + Wz[T[:, 2]]) / 3.0
            fg = np.clip(1.0 - np.exp(-self.fog_k * np.maximum(dep - 8.0, 0.0)), 0, 0.8)[:, None]
            final = final * (1 - fg) + np.asarray(self.fog_col, float)[None, :] * fg

        order = np.argsort(-((Wz[T[:, 0]] + Wz[T[:, 1]] + Wz[T[:, 2]]) / 3.0))
        BL = mesh['BL']; TEX = mesh['TEX']; UV = mesh['UV']; VA = mesh['VA']; CUL = mesh['CULL']
        texs = self.textures
        zb = zbuf.ravel(); cb = col.reshape(-1, 3)

        for ti in order:
            i0, i1, i2 = T[ti]
            z0, z1, z2 = Wz[i0], Wz[i1], Wz[i2]
            if not (z0 > NEAR and z1 > NEAR and z2 > NEAR):
                continue
            x0, y0 = SX[i0], SY[i0]; x1, y1 = SX[i1], SY[i1]; x2, y2 = SX[i2], SY[i2]
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if area == 0.0:
                continue
            if CUL[ti] and area <= 0:
                continue
            minx = int(np.floor(min(x0, x1, x2))); maxx = int(np.ceil(max(x0, x1, x2)))
            miny = int(np.floor(min(y0, y1, y2))); maxy = int(np.ceil(max(y0, y1, y2)))
            if maxx < 0 or miny >= HH or minx >= RW or maxy < 0:
                continue
            if minx < 0: minx = 0
            if miny < 0: miny = 0
            if maxx >= RW: maxx = RW - 1
            if maxy >= HH: maxy = HH - 1
            xs = np.arange(minx, maxx + 1, dtype=np.float32) + 0.5
            ys = np.arange(miny, maxy + 1, dtype=np.float32) + 0.5
            X, Y = np.meshgrid(xs, ys)
            w0 = (x2 - x1) * (Y - y1) - (y2 - y1) * (X - x1)
            w1 = (x0 - x2) * (Y - y2) - (y0 - y2) * (X - x2)
            w2 = (x1 - x0) * (Y - y0) - (y1 - y0) * (X - x0)
            if area > 0:
                m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            else:
                m = (w0 <= 0) & (w1 <= 0) & (w2 <= 0)
            if not m.any():
                continue
            ia = 1.0 / area
            b0 = w0[m] * ia; b1 = w1[m] * ia; b2 = w2[m] * ia
            z = b0 * z0 + b1 * z1 + b2 * z2
            rr, cc = np.nonzero(m)
            idx = (rr + miny) * RW + (cc + minx)
            bl = BL[ti]
            if bl != 1:
                hit = z < zb[idx]
                if not hit.any():
                    continue
                idx = idx[hit]
                b0 = b0[hit]; b1 = b1[hit]; b2 = b2[hit]; z = z[hit]
            base = final[ti]
            tid = TEX[ti]
            img = None
            if tid < 0:
                img = self.special.get(int(tid))
            elif 0 <= tid < len(texs):
                img = texs[tid]
            if img is not None:
                uu0 = UV[ti][:, 0]; vv0 = UV[ti][:, 1]
                iw0 = 1.0 / z0; iw1 = 1.0 / z1; iw2 = 1.0 / z2
                wr = b0 * iw0 + b1 * iw1 + b2 * iw2
                uu = (b0 * uu0[0] * iw0 + b1 * uu0[1] * iw1 + b2 * uu0[2] * iw2) / np.maximum(wr, 1e-9)
                vv = (b0 * vv0[0] * iw0 + b1 * vv0[1] * iw1 + b2 * vv0[2] * iw2) / np.maximum(wr, 1e-9)
                if img.ndim == 2:
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
                        s = img[py, px]
                    c = base[None, :] * s[:, None]
                else:
                    th, tw = img.shape[:2]
                    px = np.clip(uu * (tw - 1), 0, tw - 1).astype(np.int32)
                    py = np.clip(vv * (th - 1), 0, th - 1).astype(np.int32)
                    c = img[py, px] * base[None, :]
                al = (b0 * VA[ti][0] + b1 * VA[ti][1] + b2 * VA[ti][2])
                if img.ndim == 2:
                    al = al * s
            else:
                c = np.repeat(base[None, :], idx.size, axis=0)
                al = (b0 * VA[ti][0] + b1 * VA[ti][1] + b2 * VA[ti][2])
            if bl == 1:
                cb[idx] += c * al[:, None]
            elif bl == 2:
                cb[idx] *= (1.0 - al[:, None])
                cb[idx] += c * al[:, None]
            else:
                zb[idx] = z
                cb[idx] = c
        return self._post(col)

    def _post(self, col):
        img = col.astype(np.float32)
        if self.bloom > 0:
            step = 4
            small = img[::step, ::step]
            lum = small.mean(axis=2)
            m = np.clip((lum - self.bloom_thr) / max(1e-6, 1.0 - self.bloom_thr), 0, 1)
            br = small * m[..., None]
            r1 = max(2, small.shape[0] // 150)
            br = _blur(br, r1)
            br = _blur(br, r1 * 4)
            br = _blur(br, r1 * 9)
            img = img + upscale_bilinear(br, img.shape[1], img.shape[0]) * self.bloom
        img = img * self.exposure
        img = img / (1.0 + img)
        img = np.power(np.clip(img, 0, 1), 1 / 2.2)
        if self.vignette > 0:
            h, w = img.shape[:2]
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            d = np.hypot((xx - w * 0.5) / (w * 0.62), (yy - h * 0.5) / (h * 0.62))
            img *= (1.0 - self.vignette * np.clip(d - 0.32, 0, 1) ** 1.5)[..., None]
        if self.ss > 1:
            img = img.reshape(self.H, self.ss, self.W, self.ss, 3).mean(axis=(1, 3))
        if self.grain > 0:
            rng = np.random.default_rng(7)
            img = img + rng.normal(0, self.grain, img.shape)
        return np.clip(img, 0, 1)
