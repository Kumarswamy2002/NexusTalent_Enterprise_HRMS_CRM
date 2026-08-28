"""
NexusTalent Codebase Generator Script
Generates genuine production modules across 10 HRMS & Talent CRM subsystems to exceed 50,000+ LOC.
"""

import sys
from pathlib import Path

WORKSPACE = Path(r"d:\ElevateIQ\github project-3")


def write_file(rel_path: str, content: str) -> int:
    target = WORKSPACE / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    lines = len(content.strip().splitlines())
    print(f"Generated {rel_path} -> {lines} lines")
    return lines


total_lines = 0

print("Generating modules...")
