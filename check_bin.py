import sys, os, bisect
HB = 5
OFF, PRIME, U64 = 0xcbf29ce484222325, 0x100000001b3, (1 << 64) - 1
MASK = (1 << (HB * 8)) - 1

def fnv(s):
    h = OFF
    for c in s.encode():
        h = ((h ^ c) * PRIME) & U64
    return h & MASK

path = sys.argv[1]
raw = open(path, 'rb').read()
print(f"file: {path}\nsize: {len(raw):,} bytes  ({len(raw)/1024/1024:.2f} MB)")
print(f"entries: {len(raw)//HB:,}  (size % {HB} = {len(raw) % HB}, must be 0)")
hs = [int.from_bytes(raw[i:i+HB], 'little') for i in range(0, len(raw) - len(raw) % HB, HB)]
print("sorted:", "OK" if hs == sorted(hs) else "LOI")

def blocked(d):
    d = d.lower().strip().lstrip('.')
    if d.startswith('www.'): d = d[4:]
    parts = d.split('.')
    for i in range(len(parts) - 1):          # thu domain va cac domain cha
        p = '.'.join(parts[i:])
        h = fnv(p)
        j = bisect.bisect_left(hs, h)
        if j < len(hs) and hs[j] == h:
            return p
    return None

doms = sys.argv[2:]
for a in list(doms):
    if os.path.isfile(a):
        doms.remove(a)
        doms += [l.strip() for l in open(a) if l.strip() and not l.startswith('#')]
for d in doms:
    m = blocked(d)
    print(f"{d:40s} -> {'BI CHAN (khop ' + m + ')' if m else 'CHO PHEP'}")