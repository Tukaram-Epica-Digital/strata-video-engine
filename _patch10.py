import io
p = 'strata_video/scenes.py'
s = io.open(p, encoding='utf-8').read()

old = """    mesh = Mesh()
    bbs = []
    info = {}
    if t < T_VS[0]:
        if t > T_A[0] - 0.6 and t < T_TRANS[0] + 0.8:
            info['A'] = scene_A(mesh, None, t); bbs.append(info['A']['bb'])
        if t > T_TRANS[0] - 0.4 and t < T_VS[0] + 0.8:
            info['B'] = scene_B(mesh, None, t); bbs.append(info['B']['bb'])
    else:
        info['A'] = scene_A(mesh, None, t, off=(-9.6, 0, 0), s=0.60)
        info['B'] = scene_B(mesh, None, t, off=(9.6, 0, 0), s=0.60)
        bbs = [merge_bb(info['A']['bb'], info['B']['bb'])]
    if not bbs:
        bbs = [(-11.6, 12.6, 0.0, 6.2, -5.8, 2.6)]
    bb = bbs[0]
    for b in bbs[1:]:
        bb = merge_bb(bb, b)
    pts = corners(bb)
    center = np.array([(bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2 * 0.85, (bb[4] + bb[5]) / 2])
    eye, tgt = fit_view(pts, center, u, fov, W, H, SAFE, dmin=4.0, dmax=70.0)

    r = Renderer(W, H, ss=ss,
                 lights=[{'dir': (-0.35, -1.0, -0.45), 'int': 1.10, 'col': np.ones(3)},
                         {'dir': (0.8, -0.35, 0.5), 'int': 0.30, 'col': hexc('FF7A30')},
                         {'dir': (-0.7, 0.2, -0.6), 'int': 0.20, 'col': hexc('3F7FD8')}],
                 ambient=0.20, rim=0.32, exposure=1.05, bloom=0.72, bloom_thr=0.46,
                 vignette=0.24, grain=0.006, fog_col=hexc('1A0508'), fog_k=0.028)
    motherboard(mesh, r)"""
new = """    r = Renderer(W, H, ss=ss,
                 lights=[{'dir': (-0.35, -1.0, -0.45), 'int': 1.10, 'col': np.ones(3)},
                         {'dir': (0.8, -0.35, 0.5), 'int': 0.30, 'col': hexc('FF7A30')},
                         {'dir': (-0.7, 0.2, -0.6), 'int': 0.20, 'col': hexc('3F7FD8')}],
                 ambient=0.20, rim=0.32, exposure=1.05, bloom=0.72, bloom_thr=0.46,
                 vignette=0.24, grain=0.006, fog_col=hexc('1A0508'), fog_k=0.028)
    mesh = Mesh()
    bbs = []
    info = {}
    if t < T_VS[0]:
        if t > T_A[0] - 0.6 and t < T_TRANS[0] + 0.8:
            info['A'] = scene_A(mesh, r, t); bbs.append(info['A']['bb'])
        if t > T_TRANS[0] - 0.4 and t < T_VS[0] + 0.8:
            info['B'] = scene_B(mesh, r, t); bbs.append(info['B']['bb'])
    else:
        info['A'] = scene_A(mesh, r, t, off=(-9.6, 0, 0), s=0.60)
        info['B'] = scene_B(mesh, r, t, off=(9.6, 0, 0), s=0.60)
        bbs = [merge_bb(info['A']['bb'], info['B']['bb'])]
    if not bbs:
        bbs = [(-11.6, 12.6, 0.0, 6.2, -5.8, 2.6)]
    bb = bbs[0]
    for b in bbs[1:]:
        bb = merge_bb(bb, b)
    pts = corners(bb)
    center = np.array([(bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2 * 0.85, (bb[4] + bb[5]) / 2])
    eye, tgt = fit_view(pts, center, u, fov, W, H, SAFE, dmin=4.0, dmax=70.0)
    motherboard(mesh, r)"""
assert old in s, 'bloque no encontrado'
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('orden corregido')
