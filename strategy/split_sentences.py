#!/usr/bin/env python3
import re, sys
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding="utf-8").read()
t = re.sub(r"([।?])\s*", r"\1\n", t)
t = re.sub(r"(\.)\s+", r"\1\n", t)
open(dst, "w", encoding="utf-8").write(t)
print(f"{dst} -> lines: {t.count(chr(10))}")
