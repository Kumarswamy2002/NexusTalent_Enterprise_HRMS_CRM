"""
NexusTalent Enterprise 50K+ Code Generator
"""
import os
from pathlib import Path

WORKSPACE = Path(r"d:\ElevateIQ\github project-3")

def save_module(rel_path: str, code_lines: list) -> int:
    target = WORKSPACE / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(code_lines)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    return len(code_lines)

print("Module generator ready.")
