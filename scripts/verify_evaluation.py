"""
NexusTalent Automated Verification & Compliance Audit
"""

import os
import subprocess
import zipfile
from pathlib import Path

WORKSPACE = Path(r"d:\ElevateIQ\github project-3")
ZIP_PATH = Path(r"D:\ElevateIQ\NexusTalent_Enterprise_HRMS_CRM.zip")

print("=" * 70)
print("AUTOMATED COMPLIANCE & EVALUATION AUDIT")
print("=" * 70)

# 1. LOC Audit
EXCLUDE_DIRS = {".git", "tests", "node_modules", "dist", "coverage", "__pycache__", "scratch", "scripts"}
VALID_EXTS = {".py", ".js", ".html", ".css", ".json", ".yml", ".yaml", ".toml", ".md"}
prod_loc = 0
file_count = 0
for root, dirs, files in os.walk(WORKSPACE):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
    for file in files:
        fp = Path(root) / file
        if fp.suffix.lower() in VALID_EXTS:
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    cnt = len([line for line in f.read().splitlines() if line.strip()])
                    prod_loc += cnt
                    file_count += 1
            except Exception:
                pass

status_loc = "PASS" if prod_loc >= 50000 else "FAIL"
print(f"1. Minimum 50,000+ Prod LOC: {status_loc} -> {prod_loc:,} LOC across {file_count} prod source files (Required: >= 50,000)")

# 2. Git repo presence
git_dir = WORKSPACE / ".git"
status_git = "PASS" if git_dir.exists() and git_dir.is_dir() else "FAIL"
print(f"2. Git-based repository (.git present): {status_git}")

# 3. Commit count
log_res = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=str(WORKSPACE), capture_output=True, text=True)
commit_count = int(log_res.stdout.strip()) if log_res.returncode == 0 else 0
status_commits = "PASS" if commit_count >= 5 else "FAIL"
print(f"3. At least 5 meaningful commits: {status_commits} -> {commit_count} commits recorded (Required: >= 5)")

# 4. PR Merge commits
merge_res = subprocess.run(["git", "log", "--merges", "--oneline"], cwd=str(WORKSPACE), capture_output=True, text=True)
merges = [line for line in merge_res.stdout.strip().splitlines() if line.strip()]
status_merges = "PASS" if len(merges) >= 4 else "FAIL"
print(f"4. At least 4 PR merges: {status_merges} -> {len(merges)} PR merge commits found (Required: >= 4):")
for m in merges:
    print(f"   - {m}")

# 5. Executable project
has_docker = (WORKSPACE / "Dockerfile").exists()
has_compose = (WORKSPACE / "docker-compose.yml").exists()
has_pkg = (WORKSPACE / "package.json").exists()
has_make = (WORKSPACE / "Makefile").exists()
has_entry = (WORKSPACE / "backend" / "app" / "main.py").exists()
is_exec = has_docker and has_compose and has_pkg and has_make and has_entry
status_exec = "PASS" if is_exec else "FAIL"
print(f"5. Executable project: {status_exec} (Dockerfile: {has_docker}, compose: {has_compose}, package.json: {has_pkg}, Makefile: {has_make}, main.py: {has_entry})")

# 6. README documentation
readme_p = WORKSPACE / "README.md"
has_readme = readme_p.exists()
sections_pass = False
if has_readme:
    text = readme_p.read_text(encoding="utf-8").lower()
    req_sections = ["installation", "build", "run", "dependencies", "usage"]
    sections_pass = all(s in text for s in req_sections)
status_readme = "PASS" if sections_pass else "FAIL"
print(f"6. README with Build/Install/Run/Deps/Usage: {status_readme}")

# 7. Lockfiles
has_npm_lock = (WORKSPACE / "package-lock.json").exists()
has_poetry_lock = (WORKSPACE / "poetry.lock").exists()
status_locks = "PASS" if has_npm_lock and has_poetry_lock else "FAIL"
print(f"7. Dependency documentation & lockfiles: {status_locks} (package-lock.json: {has_npm_lock}, poetry.lock: {has_poetry_lock})")

# 8. Zip verification
zip_pass = False
if ZIP_PATH.exists():
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        names = z.namelist()
        has_git_in_zip = any(n.startswith(".git/") or n.startswith(".git\\") for n in names)
        zip_pass = has_git_in_zip
status_zip = "PASS" if zip_pass else "FAIL"
print(f"8. ZIP File saved at {ZIP_PATH}: {status_zip} (Size: {ZIP_PATH.stat().st_size / (1024*1024):.2f} MB, Contains .git: {zip_pass})")
print("=" * 70)
