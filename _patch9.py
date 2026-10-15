import io

p = 'strata_video/props.py'
s = io.open(p, encoding='utf-8').read()
old = """def motherboard(mesh, renderer):
    tid = renderer.tex(board_grid(512, 24, 0.10, 0.015))
    mesh.quad(np.array([-15, 0, -10]), np.array([15, 0, -10]), np.array([15, 0, 10]),
              np.array([-15, 0, 10]), hexc('2A0F10'), 0.0, OPAQUE, 1.0, tid,
              [[0, 0], [1, 0], [1, 1], [0, 1]])
    for (x, z, sx, sz) in [(-15, 0, 0.16, 20), (15, 0, 0.16, 20), (0, -10, 30, 0.16), (0, 10, 30, 0.16)]:
        mesh.box((x, 0.08, z), (sx, 0.16, sz), hexc('4A2A22'), 0.0)
    rng = np.random.default_rng(4)
    for _ in range(30):"""
new = """def motherboard(mesh, renderer):
    # placa oscura: insinua el hardware, no domina el cuadro
    tid = renderer.tex(board_grid(512, 26, 0.055, 0.006))
    mesh.quad(np.array([-13, 0, -9]), np.array([13, 0, -9]), np.array([13, 0, 7]),
              np.array([-13, 0, 7]), hexc('120709'), 0.0, OPAQUE, 1.0, tid,
              [[0, 0], [1, 0], [1, 1], [0, 1]])
    for (x, z, sx, sz) in [(-13, -1, 0.14, 16), (13, -1, 0.14, 16), (0, -9, 26, 0.14), (0, 7, 26, 0.14)]:
        mesh.box((x, 0.07, z), (sx, 0.14, sz), hexc('2A1712'), 0.0)
    rng = np.random.default_rng(4)
    for _ in range(18):"""
assert old in s, 'motherboard no encontrado'
s = s.replace(old, new)
s = s.replace("        x = rng.uniform(-14, 14); z = rng.uniform(-9, 9)",
              "        x = rng.uniform(-12, 12); z = rng.uniform(-8, 6)")
io.open(p, 'w', encoding='utf-8').write(s)
print('props ok')

p2 = 'strata_video/scenes.py'
t = io.open(p2, encoding='utf-8').read()
t = t.replace("""                 ambient=0.22, rim=0.5, exposure=1.02, bloom=0.75, bloom_thr=0.45,
                 vignette=0.24, grain=0.006)""",
"""                 ambient=0.20, rim=0.32, exposure=1.05, bloom=0.72, bloom_thr=0.46,
                 vignette=0.24, grain=0.006,
                 fog_col=hexc('1A0508'), fog_k=0.030)""")
t = t.replace("'center': a + np.array([0.4 * s, 2.4 * s, -1.4 * s]), 'radius': 11.5 * s,",
              "'center': a + np.array([0.4 * s, 2.2 * s, -1.2 * s]), 'radius': 9.6 * s,")
t = t.replace("'center': a + np.array([0.4 * s, 2.6 * s, -1.6 * s]), 'radius': 11.5 * s,",
              "'center': a + np.array([0.4 * s, 2.4 * s, -1.4 * s]), 'radius': 9.6 * s,")
t = t.replace("rad = lerp(26.0, 11.5, p)", "rad = lerp(21.0, 9.6, p)")
t = t.replace("rad = 11.5", "rad = 9.6")
t = t.replace("rad = lerp(11.5, 19.0, ease(p))", "rad = lerp(9.6, 16.5, ease(p))")
t = t.replace("rad = lerp(19.0, 16.0, p)", "rad = lerp(16.5, 14.0, p)")
io.open(p2, 'w', encoding='utf-8').write(t)
print('scenes ok')
