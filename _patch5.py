import io
p = 'strata_video/scenes.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace("def build_frame(i, W, H, ss=1):", "def build_frame(i, W, H, ss=1, no_bg=False):")
s = s.replace("    img = r.render(mesh, eye, tgt, fov, bg=bgimg)",
              "    img = r.render(mesh, eye, tgt, fov, bg=(None if no_bg else bgimg))")
io.open(p, 'w', encoding='utf-8').write(s)
print('ok', 'no_bg' in s)
