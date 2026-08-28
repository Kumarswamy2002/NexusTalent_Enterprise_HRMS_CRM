"""
NexusTalent Enterprise Full Subsystem Code Synthesizer
"""

import os
from pathlib import Path

WORKSPACE = Path(r"d:\ElevateIQ\github project-3")


def create_file(rel_path: str, content: str) -> int:
    target = WORKSPACE / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    lines = len(content.strip().splitlines())
    return lines


print("🛠️ Module generator initialized.")
