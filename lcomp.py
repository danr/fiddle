import sys
import dis
assert sys.version_info[0] >= 3
assert sys.version_info[1] >= 11
u = 1
xs = [1,2,3]
g = (
    x + u + y
    for x in xs
    for y in xs
)
text = open(__file__, 'r').read()
lines = text.splitlines()
for coords in g.gi_code.co_positions():
    y0, y1, x0, x1 = coords
    if any(x is None for x in coords):
        continue
    if y0 != y1:
        lin = [
            lines[y0-1][x0:],
            *lines[y0:y1-1],
            lines[y1-1][:x1],
        ]
    else:
        lin = [
            lines[y0-1][x0:x1],
        ]
    print(
        *coords, ' '.join(lin)
    )

dis.disassemble(g.gi_code)

print(g.gi_frame)
