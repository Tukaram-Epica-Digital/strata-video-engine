"""Motor 3D procedural (numpy puro). Matematicas, malla, texturas, PNG."""
import numpy as np
import zlib, struct, os

NEAR = 0.05
ADD, OPAQUE, MUL = 1, 0, 2

# ------------------------------------------------------------------ mates
def norm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def look_at(eye, target, up=(0, 1, 0)):
    eye = np.asarray(eye, float); target = np.asarray(target, float)
    f = norm(target - eye)
    r = norm(np.cross(f, np.asarray(up, float)))
    u = np.cross(r, f)
    R = np.stack([r, u, f])   # z de camara crece hacia delante
    return R, -R @ eye


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def smoothstep(a, b, x):
    t = clamp01((x - a) / max(1e-9, b - a))
    return t * t * (3 - 2 * t)


def ease(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * float(t)


def cr(p0, p1, p2, p3, t):
    return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def spline(pts, u):
    pts = [np.asarray(p, float) for p in pts]
    n = len(pts)
    if n == 1:
        return pts[0]
    u = clamp01(u) * (n - 1)
    i = int(min(n - 2, u)); t = u - i
    return cr(pts[max(0, i - 1)], pts[i], pts[min(n - 1, i + 1)], pts[min(n - 1, i + 2)], t)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def sc(v, k):
    return np.asarray(v, float) * float(k)


# Paleta tomada de FONDO.png del canal
BG0 = hexc('14040A')
BG1 = hexc('3A0A08')
AMBER = hexc('FF8A1E')
GOLD = hexc('FFC24A')
HOT = hexc('FFEBC2')
RED = hexc('E8342B')
DIM = hexc('5A1A16')
CYAN = hexc('3FA8FF')
ICE = hexc('A8E8FF')
WHITE = np.array([1.0, 1.0, 1.0])
STEEL = hexc('241318')
STEEL2 = hexc('3E2429')


# ------------------------------------------------------------------ malla
class Mesh:
    def __init__(self):
        self.V, self.T = [], []
        self.COL, self.EM, self.BL, self.TEX, self.UV, self.CULL, self.VA = [], [], [], [], [], [], []

    def tri(self, p0, p1, p2, color, emis=0.0, bl=0, alpha=1.0, tex=-1, uvs=None, cull=False):
        i = len(self.V)
        self.V += [p0, p1, p2]
        self.T.append((i, i + 1, i + 2))
        self.COL.append(np.asarray(color, float))
        self.EM.append(float(emis)); self.BL.append(int(bl)); self.TEX.append(int(tex))
        self.UV.append([[0, 0], [1, 0], [1, 1]] if uvs is None else list(uvs))
        self.CULL.append(bool(cull))
        self.VA.append([alpha] * 3 if np.isscalar(alpha) else list(alpha))

    def quad(self, a, b, c, d, color, emis=0.0, bl=0, alpha=1.0, tex=-1, uvs=None, cull=False):
        al = [alpha] * 4 if np.isscalar(alpha) else list(alpha)
        u1 = None if uvs is None else [uvs[0], uvs[1], uvs[2]]
        u2 = None if uvs is None else [uvs[0], uvs[2], uvs[3]]
        self.tri(a, b, c, color, emis, bl, [al[0], al[1], al[2]], tex, u1, cull)
        self.tri(a, c, d, color, emis, bl, [al[0], al[2], al[3]], tex, u2, cull)

    def rect(self, pos, w, h, color, emis=0.0, bl=0, alpha=1.0, tex=-1, n=(1, 0, 0)):
        """plano centrado en pos con normal n"""
        n = norm(np.asarray(n, float))
        ref = np.array([0.0, 1.0, 0.0]) if abs(n[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        u = np.cross(n, ref); u = u / np.linalg.norm(u)
        v = np.cross(n, u)
        p = np.asarray(pos, float)
        hw, hh = float(w) * 0.5, float(h) * 0.5
        uv = [[0, 0], [1, 0], [1, 1], [0, 1]]
        self.quad(p - u * hw - v * hh, p + u * hw - v * hh, p + u * hw + v * hh, p - u * hw + v * hh,
                  color, emis, bl, alpha, tex, uv)

    def box(self, pos, size, color, emis=0.0, rot=None, bl=0, alpha=1.0):
        s = np.asarray(size, float) * 0.5
        cn = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                       [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float) * s
        if rot is not None:
            cn = cn @ np.asarray(rot, float).T
        cn = cn + np.asarray(pos, float)
        F = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)]
        for f in F:
            self.quad(cn[f[0]], cn[f[1]], cn[f[2]], cn[f[3]], color, emis, bl, alpha)

    def wire(self, pos, size, color, thick, emis=1.0, rot=None, bl=ADD):
        s = np.asarray(size, float) * 0.5
        cn = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                       [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float) * s
        if rot is not None:
            cn = cn @ np.asarray(rot, float).T
        cn = cn + np.asarray(pos, float)
        E = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
        for a, b in E:
            self.bar(cn[a], cn[b], thick, color, emis, bl)

    def bar(self, p0, p1, t, color, emis=1.0, bl=ADD):
        p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
        d = p1 - p0
        L = np.linalg.norm(d)
        if L < 1e-6:
            return
        d = d / L
        ref = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        u = np.cross(d, ref); u = u / np.linalg.norm(u) * (t * 0.5)
        v = np.cross(d, u); v = v / np.linalg.norm(v) * (t * 0.5)
        a0, a1, a2, a3 = p0 - u - v, p0 + u - v, p0 + u + v, p0 - u + v
        b0, b1, b2, b3 = p1 - u - v, p1 + u - v, p1 + u + v, p1 - u + v
        for f in [(a0, a1, b1, b0), (a1, a2, b2, b1), (a2, a3, b3, b2), (a3, a0, b0, b3)]:
            self.quad(f[0], f[1], f[2], f[3], color, emis, bl)

    def ribbon(self, path, width, color, alpha=1.0, emis=1.0, up=(0, 1, 0), bl=ADD):
        path = [np.asarray(p, float) for p in path]
        if len(path) < 2:
            return
        w = np.asarray(width, float) if np.ndim(width) else np.full(len(path), float(width))
        al = np.asarray(alpha, float) if np.ndim(alpha) else np.full(len(path), float(alpha))
        sm = [path[0]]
        for i in range(1, len(path) - 1):
            sm.append(0.25 * path[i - 1] + 0.5 * path[i] + 0.25 * path[i + 1])
        sm.append(path[-1])
        up = np.asarray(up, float)
        for i in range(len(sm) - 1):
            d = sm[i + 1] - sm[i]
            L = np.linalg.norm(d)
            if L < 1e-9:
                continue
            d = d / L
            n = np.cross(d, up)
            if np.linalg.norm(n) < 1e-6:
                n = np.cross(d, np.array([1.0, 0, 0]))
            n = n / np.linalg.norm(n)
            self.quad(sm[i] - n * w[i] * 0.5, sm[i] + n * w[i] * 0.5,
                      sm[i + 1] + n * w[i + 1] * 0.5, sm[i + 1] - n * w[i + 1] * 0.5,
                      color, emis, bl, [al[i], al[i], al[i + 1], al[i + 1]])

    def bb(self, pos, size, color, alpha=1.0, emis=1.0, R=None, tex=-1):
        p = np.asarray(pos, float); s = float(size)
        if R is None:
            r, u = np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
        else:
            r, u = np.asarray(R, float)[0], np.asarray(R, float)[1]
        uv = [[0, 0], [1, 0], [1, 1], [0, 1]]
        self.quad(p - r * s - u * s, p + r * s - u * s, p + r * s + u * s, p - r * s + u * s,
                  color, emis, ADD, [alpha] * 4, tex, uv)

    def finish(self):
        return {
            'V': np.asarray(self.V, float).reshape(-1, 3),
            'T': np.asarray(self.T, int).reshape(-1, 3),
            'COL': np.asarray(self.COL, float).reshape(-1, 3),
            'EM': np.asarray(self.EM, float),
            'BL': np.asarray(self.BL, int),
            'TEX': np.asarray(self.TEX, int),
            'UV': np.asarray(self.UV, float).reshape(-1, 3, 2),
            'CULL': np.asarray(self.CULL, bool),
            'VA': np.asarray(self.VA, float).reshape(-1, 3),
        }


# ------------------------------------------------------------------ texturas
_cache = {}


def radial(size=96, power=2.0):
    k = ('r', size, power)
    if k in _cache:
        return _cache[k]
    y, x = np.mgrid[0:size, 0:size].astype(float)
    d = np.hypot(x - size / 2, y - size / 2) / (size * 0.5)
    _cache[k] = np.clip(1 - d, 0, 1) ** power
    return _cache[k]


def soft_rect(w, h, feather=0.18):
    k = ('sr', w, h, feather)
    if k in _cache:
        return _cache[k]
    y, x = np.mgrid[0:h, 0:w].astype(float)
    dx = np.minimum(x, w - 1 - x) / (w * feather)
    dy = np.minimum(y, h - 1 - y) / (h * feather)
    a = np.clip(np.minimum(dx, dy), 0, 1)
    _cache[k] = a
    return _cache[k]


def cell_grid(cols, rows, cell=5, gap=2, base=0.10, frame=0.02):
    """panel de celdas (1 canal). Devuelve array HxW."""
    W = cols * (cell + gap) + gap
    H = rows * (cell + gap) + gap
    img = np.full((H, W), frame, float)
    for r in range(rows):
        y0 = gap + r * (cell + gap)
        for c in range(cols):
            x0 = gap + c * (cell + gap)
            img[y0:y0 + cell, x0:x0 + cell] = base
    return img


def board_grid(size=512, step=16, line=0.16, base=0.03):
    k = ('bg', size, step, line, base)
    if k in _cache:
        return _cache[k]
    img = np.full((size, size), base, float)
    idx = np.arange(size)
    mask = (idx % step) < 1
    img[mask, :] = np.maximum(img[mask, :], line)
    img[:, mask] = np.maximum(img[:, mask], line)
    _cache[k] = img
    return _cache[k]


# ------------------------------------------------------------------ PNG
def png_write(path, img):
    a = (np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    h, w, _ = a.shape
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += a[y].tobytes()

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)))
        f.write(chunk(b'IDAT', zlib.compress(bytes(raw), 4)))
        f.write(chunk(b'IEND', b''))


def png_read(path):
    """decodificador PNG minimo (8 bits, RGB/gray, sin interlace) -> float 0..1"""
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n'
    i = 8
    idat = b''
    w = h = ct = bd = None
    while i < len(d):
        ln = struct.unpack('>I', d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        data = d[i + 8:i + 8 + ln]
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[:10])
        elif typ == b'IDAT':
            idat += data
        elif typ == b'IEND':
            break
        i += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 6: 4}[ct]
    assert bd == 8
    stride = w * ch
    out = np.zeros((h, w, ch), np.uint8)
    prev = np.zeros(stride, np.uint8)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = np.frombuffer(raw[p:p + stride], np.uint8).copy(); p += stride
        if f == 0:
            cur = line
        elif f == 1:
            cur = line
            for x in range(ch, stride):
                cur[x] = (cur[x] + cur[x - ch]) & 255
        elif f == 2:
            cur = (line.astype(np.uint16) + prev).astype(np.uint8)
        elif f == 3:
            cur = line
            for x in range(stride):
                a = cur[x - ch] if x >= ch else 0
                cur[x] = (int(line[x]) + ((int(a) + int(prev[x])) >> 1)) & 255
        elif f == 4:
            cur = line
            for x in range(stride):
                a = cur[x - ch] if x >= ch else 0
                b = prev[x]
                c = prev[x - ch] if x >= ch else 0
                pp = int(a) + int(b) - int(c)
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[x] = (int(line[x]) + pr) & 255
        out[y] = cur
        prev = cur
    img = out[:, :, :3].astype(float) / 255.0
    return img
