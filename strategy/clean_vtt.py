#!/usr/bin/env python3
"""Clean YouTube auto-caption VTT (Hindi) into one continuous, de-duplicated text file."""
import re, sys

src = sys.argv[1] if len(sys.argv) > 1 else "strategy/ict-session.hi.vtt"
dst = sys.argv[2] if len(sys.argv) > 2 else "strategy/ict-session.clean.txt"

raw = open(src, encoding="utf-8").read().splitlines()
out = []
last = None
for line in raw:
    if line.startswith(("WEBVTT", "Kind:", "Language:")):
        continue
    if "-->" in line:
        continue
    line = re.sub(r"<[^>]+>", "", line)        # strip inline <...> timestamp/<c> tags
    line = re.sub(r"\s+", " ", line).strip()
    if not line:
        continue
    if re.fullmatch(r"\[.*\]", line):           # [संगीत] / [music] etc.
        continue
    if line == last:                            # drop exact consecutive duplicate
        continue
    # drop if this line is just the previous line + appended words (rolling growth)
    if last and line.startswith(last):
        out[-1] = line
        last = line
        continue
    out.append(line)
    last = line

text = " ".join(out)
text = re.sub(r"\s+", " ", text).strip()
open(dst, "w", encoding="utf-8").write(text + "\n")
print(f"lines kept: {len(out)}")
print(f"chars: {len(text)}")
print(f"words (approx): {len(text.split())}")
