import io
p = 'strata_video/raster.py'
s = io.open(p, encoding='utf-8').read()
# modo aditivo sin test de profundidad (rotulos siempre visibles)
s = s.replace("""            bl = BL[ti]
            if bl != 1:""", """            bl = BL[ti]
            if bl not in (1, 3):""")
s = s.replace("""            if bl == 1:
                cb[idx] += c * al[:, None]""", """            if bl in (1, 3):
                cb[idx] += c * al[:, None]""")
io.open(p, 'w', encoding='utf-8').write(s)
print('ok')
