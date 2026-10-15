import io
p = 'strata_video/engine.py'
s = io.open(p, encoding='utf-8').read()
old = """    R = np.stack([r, u, -f])
    return R, -R @ eye"""
new = """    R = np.stack([r, u, f])   # z de camara crece hacia delante
    return R, -R @ eye"""
assert old in s, 'no encontrado'
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('parcheado')
