import gzip
from pathlib import Path


Import("env")

project = Path(env.subst("$PROJECT_DIR"))
build = Path(env.subst("$BUILD_DIR"))
page = (project / "src" / "page.html").read_bytes()
compressed = gzip.compress(page, compresslevel=9, mtime=0)

header = ["#pragma once", "const uint8_t PAGE[] PROGMEM = {"]
for start in range(0, len(compressed), 16):
    values = (f"0x{byte:02x}" for byte in compressed[start:start + 16])
    header.append("  " + ", ".join(values) + ",")
header.append("};")

output = build / "page.h"
output.write_text("\n".join(header) + "\n", encoding="ascii")
env.Append(CPPPATH=[str(build)])
