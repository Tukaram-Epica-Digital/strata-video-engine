import io
p = 'strata_video/scenes.py'
s = io.open(p, encoding='utf-8').read()
old = "    L = Labels(mesh, r, R, eye, fov, H)"
new = "    L = Labels(mesh, r, R, eye, tgt, fov, W, H)"
assert old in s
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('ok')
