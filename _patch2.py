import io
p = 'strata_video/scenes.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace("    tt = t - T_A[0]", "    tt = max(0.0, t - T_A[0])")
s = s.replace("    tt = t - T_B[0]", "    tt = max(0.0, t - T_B[0])")
io.open(p, 'w', encoding='utf-8').write(s)
print('ok')
