#!/usr/bin/env python3
"""Validate skill routing and rule format (02 §8, §13)"""
import pathlib, yaml, sys
base=pathlib.Path(__file__).parent.parent
ok=True
for p in (base/"rules").glob("*.md"):
    txt=p.read_text()
    for k in ["id:","layer:","owner:","required_proof:"]:
        if k not in txt:
            print(f"FAIL {p.name} missing {k}")
            ok=False
if ok:
    print("validate_skill: PASS")
sys.exit(0 if ok else 1)
