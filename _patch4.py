import io
p = 'strata_video/raster.py'
s = io.open(p, encoding='utf-8').read()
old = """            if bl != 1:
                hit = z < zb[idx]
                if not hit.any():
                    continue
                idx = idx[hit]"""
new = """            if bl != 1:
                hit = z < zb[idx]
                if not hit.any():
                    continue
                idx = idx[hit]
                b0 = b0[hit]; b1 = b1[hit]; b2 = b2[hit]; z = z[hit]"""
assert old in s
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('ok')
