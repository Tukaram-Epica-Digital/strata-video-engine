import io, sys
p = 'strata_video/props.py'
t = io.open(p, encoding='utf-8').read()
t = t.replace("from engine import (Mesh, OPAQUE, ADD, norm, sc, hexc, radial, board_grid, soft_rect)",
              "from engine import (Mesh, OPAQUE, ADD, norm, sc, hexc, radial, board_grid, soft_rect)\n"
              "from raster import TEX_GLOW, TEX_DOT, TEX_SOFT")
t = t.replace("1.0, -5)", "1.0, TEX_GLOW)")
t = t.replace("0.15, -1)", "0.15, TEX_DOT)")
t = t.replace("1.0, -6)", "1.0, TEX_SOFT)")
io.open(p, 'w', encoding='utf-8').write(t)
print([l for l in t.split('\n') if 'TEX_' in l])

p2 = 'strata_video/scenes.py'
s = io.open(p2, encoding='utf-8').read()
s = s.replace("from raster import Renderer", "from raster import Renderer, TEX_GLOW")
s = s.replace("small = bgmod.background(t, bw, bh)\n    yi = np.linspace(0, bh - 1, H).astype(np.int32)\n    xi = np.linspace(0, bw - 1, W).astype(np.int32)\n    bgimg = small[yi[:, None], xi[None, :], :]",
              "small = bgmod.background(t, bw, bh)\n    from raster import upscale_bilinear\n    bgimg = upscale_bilinear(small, W, H)")
io.open(p2, 'w', encoding='utf-8').write(s)
print('bg patched:', 'upscale_bilinear' in s)
