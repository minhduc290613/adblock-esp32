#!/usr/bin/env python3
"""Preprocess hosts/domain blocklists into a sorted truncated-FNV-1a hash blob
for the ESP32-C3 ad-blocker. Hashes live in flash and are binary-searched on the
device, so no PSRAM is needed.

HASH_BYTES MUST match the firmware (src/main.cpp). 5 bytes (40-bit) keeps
~0 collisions up to ~500k domains while fitting half a million in <3 MB.

Usage: build_blocklist.py [out.bin] [src ...]
  src = local file or URL. With none given, downloads a balanced daily-driver set
  (StevenBlack base + Hagezi Light + AdGuard Allowlist) ~= 100k entries: blocks ads/trackers/malware
  but leaves WhatsApp/Instagram/social/messaging working.

  For the aggressive "test the limits" build (~500k, also blocks social/messaging):
    build_blocklist.py blocklist.bin \
      https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn-social/hosts \
      https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/pro.mini-onlydomains.txt \
      https://raw.githubusercontent.com/8technologia/adguardhome/refs/heads/main/allowlists.txt
"""
import re
import sys, os, math, urllib.request

HASH_BYTES = 5                          # 40-bit hashes -- must match firmware
MASK = (1 << (HASH_BYTES * 8)) - 1
FNV_OFFSET = 0xcbf29ce484222325
FNV_PRIME  = 0x100000001b3
U64 = (1 << 64) - 1

# Danh sách nguồn mặc định (Bao gồm cả danh sách Chặn và danh sách Cho phép / Allowlist):
DEFAULT_SOURCES = [
    # 1. Blocklists
    'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts',            # base: ads + malware
    'https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/light-onlydomains.txt',  # Hagezi Light

    # 2. Allowlists (Whitelist) - tự động gỡ bỏ các domain bị block nhầm
    'https://raw.githubusercontent.com/8technologia/adguardhome/refs/heads/main/allowlists.txt',
    # Bạn có thể thêm các link allowlist khác vào đây, ví dụ:
    # 'https://raw.githubusercontent.com/anudeepND/whitelist/master/domains/whitelist.txt',
]

# ||domain^  or  @@||domain^  optionally followed by $modifiers
ADG = re.compile(r'^(@@)?\|\|([a-z0-9._-]+)\^?(\$.*)?$', re.I)

ALLOW_MISSING = False

def fnv(b: bytes) -> int:
    h = FNV_OFFSET
    for c in b:
        h = ((h ^ c) * FNV_PRIME) & U64
    return h & MASK                      # truncate to HASH_BYTES

def norm(d: str) -> str:
    d = d.strip().lower().lstrip('*').lstrip('.').rstrip('.')
    return d[4:] if d.startswith('www.') else d

def read_source(src: str) -> str:
    if os.path.exists(src):
        return open(src, errors='ignore').read()
    print(f'  downloading {src} ...', file=sys.stderr)
    return urllib.request.urlopen(src, timeout=180).read().decode('utf-8', 'ignore')

def main():
    global ALLOW_MISSING
    args = [a for a in sys.argv[1:] if a != '--allow-missing']
    ALLOW_MISSING = '--allow-missing' in sys.argv[1:]
    out = args[0] if args else 'blocklist.bin'
    sources = args[1:] if len(args) > 1 else DEFAULT_SOURCES

    domains, allow = set(), set()
    skipped = 0
    for src in sources:
        try:
            data = read_source(src)
        except Exception as e:
            print(f'  !! FAILED to read {src}: {e}', file=sys.stderr)
            if not ALLOW_MISSING: sys.exit(1)
            continue
            
        for line in data.splitlines():
            line = line.strip()
            if not line or line.startswith('!'):
                continue
                
            # Xử lý comment nhưng giữ nguyên các quy tắc adblock (bắt đầu bằng ||, @@, |)
            if not line.startswith(('||', '@@', '|')):
                line = line.split('#', 1)[0].strip()
                if not line:
                    continue

            # Xử lý quy tắc AdGuard / ABP: ||example.com^ và allowlist @@||example.com^
            m = ADG.match(line)
            if m:
                if m.group(3):            # Bỏ qua nếu chứa $modifiers (client, dnstype, ...)
                    skipped += 1
                    continue
                d_norm = norm(m.group(2))
                if d_norm:
                    (allow if m.group(1) else domains).add(d_norm)
                continue
                
            if line.startswith(('||', '@@', '|')) or any(c in line for c in '^$*'):
                skipped += 1
                continue                  # Bỏ qua cú pháp adblock không tương thích với DNS hash list
                
            # Xử lý cú pháp file hosts truyền thống (0.0.0.0 domain)
            parts = line.split()
            if not parts:
                continue
            if parts[0] in ('0.0.0.0', '127.0.0.1', '::1', '::'):
                entries = parts[1:]
            else:
                entries = parts if len(parts) == 1 else []
                
            for d in entries:
                d = norm(d)
                if '.' in d and ' ' not in d:
                    domains.add(d)

    # Loại bỏ các domain thuộc Whitelist
    if allow:
        before = len(domains)
        
        # 1. Trừ trực tiếp các domain trùng khớp hoàn toàn
        domains -= allow
        
        # 2. Xử lý subdomain: nếu allow domain gốc (ví dụ: google.com), 
        # tự động gỡ tất cả subdomain của nó khỏi danh sách block (ví dụ: mail.google.com)
        to_remove = set()
        for a in allow:
            for d in domains:
                if d.endswith('.' + a):
                    to_remove.add(d)
        domains -= to_remove
        
        print(f'allowlisted      : {before - len(domains):,} removed ({len(allow):,} @@ rules)', file=sys.stderr)

    if skipped:
        print(f'skipped rules    : {skipped:,} (adblock syntax that a DNS hash list cannot express)', file=sys.stderr)

    hashes = sorted(fnv(d.encode()) for d in domains)
    collisions = len(hashes) - len(set(hashes))
    uniq = sorted(set(hashes))            # Mỗi hash giữ 1 giá trị duy nhất

    with open(out, 'wb') as f:
        for h in uniq:
            f.write(h.to_bytes(HASH_BYTES, 'little'))

    n, size = len(uniq), len(uniq) * HASH_BYTES
    print(f'source domains   : {len(domains):,}')
    print(f'hash entries     : {n:,}  ({HASH_BYTES}-byte / {HASH_BYTES*8}-bit)')
    print(f'collisions       : {collisions}  (domains sharing a hash -> over-block)')
    print(f'flash blob       : {size:,} bytes  ({size/1024/1024:.2f} MB)  -> {out}')
    print(f'lookup           : ~{math.ceil(math.log2(max(n,2)))} reads/query')

if __name__ == '__main__':
    main()