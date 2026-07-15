#!/usr/bin/env python3
"""server_doctor.py — diagnose and fix the deployed Django app.

Idempotent: every step checks current state first and only acts when needed.
Runs against the checkout it lives in, regardless of the working directory.

In cPanel's "Execute python script" box, enter:

    /home/slnkhczw/repositories/successful_safaris/backend/server_doctor.py

Options (append after the path):
    --pull      also run `git pull --ff-only` in this checkout first
    --dry-run   report problems but change nothing
"""

import getpass
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

DRY_RUN = "--dry-run" in sys.argv[1:]
DO_PULL = "--pull" in sys.argv[1:]
unknown = [a for a in sys.argv[1:] if a not in ("--dry-run", "--pull")]
if unknown:
    print(f"Unknown option(s): {' '.join(unknown)}")
    sys.exit(2)

changed = False
failed = False
pending = False  # fixes that would run, but were skipped by --dry-run


def ok(msg):
    print(f"  [OK]    {msg}", flush=True)


def fixed(msg):
    global changed
    changed = True
    print(f"  [FIXED] {msg}", flush=True)


def skip(msg):
    print(f"  [SKIP]  {msg}", flush=True)


def would(msg):
    global pending
    pending = True
    print(f"  [WOULD] {msg}", flush=True)


def warn(msg):
    print(f"  [WARN]  {msg}", flush=True)


def fail(msg):
    global failed
    failed = True
    print(f"  [FAIL]  {msg}", flush=True)


def section(title):
    print(f"== {title} ==", flush=True)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=APP_DIR, **kw)


# ---------------------------------------------------------------- environment
section("Environment")
print(f"  invoked from : {os.getcwd()}")
print(f"  app dir      : {APP_DIR}")
print(f"  user/host    : {getpass.getuser()}@{socket.gethostname()}")

if not (APP_DIR / "manage.py").exists():
    fail("manage.py not found next to this script — is it inside backend/?")
    sys.exit(1)
os.chdir(APP_DIR)

# The two-checkout trap: running collectstatic in the wrong copy does nothing.
home = Path.home()
others = [
    p for p in home.glob("*/*/passenger_wsgi.py")
    if p.parent != APP_DIR
] + [
    p for p in home.glob("*/*/*/passenger_wsgi.py")
    if p.parent != APP_DIR
]
if others:
    warn("other checkout(s) found — make sure the WSGI app points at THIS one:")
    for p in others[:3]:
        print(f"          {p}")

# ---------------------------------------------------------------- python
section("Python")
pyver = sys.version_info
print(f"  python       : {sys.executable} (Python {pyver.major}.{pyver.minor}.{pyver.micro})")
if pyver < (3, 10):
    fail(f"Python {pyver.major}.{pyver.minor} is too old for this project (needs >= 3.10).")
    rel = APP_DIR.relative_to(home) if APP_DIR.is_relative_to(home) else APP_DIR
    print(f"          Run this script with the app's venv python under: {home}/virtualenv/{rel}/")
    sys.exit(1)
ok("Python version is supported")

# ---------------------------------------------------------------- dependencies
section("Dependencies")
try:
    import django  # noqa: F401
    import dotenv  # noqa: F401
    import whitenoise  # noqa: F401
    ok("core packages importable (django, whitenoise, dotenv)")
except ImportError as exc:
    requirements = APP_DIR / "requirements.txt"
    if not requirements.exists():
        fail(f"missing package ({exc.name}) and no requirements.txt to install from")
        sys.exit(1)
    if DRY_RUN:
        would(f"pip install -r requirements.txt (missing: {exc.name})")
        fail("django not importable; later checks can't run in dry-run without it")
        sys.exit(1)
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements)])
    if result.returncode == 0:
        fixed("installed dependencies from requirements.txt")
        import django  # noqa: F401
    else:
        fail("pip install failed — check the output above")
        sys.exit(1)

# ---------------------------------------------------------------- git
section("Git")
if run(["git", "rev-parse", "--git-dir"]).returncode == 0:
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    commit = run(["git", "log", "--oneline", "-1"]).stdout.strip()
    print(f"  branch       : {branch}")
    print(f"  commit       : {commit}")
    if DO_PULL:
        if DRY_RUN:
            would("git pull --ff-only")
        else:
            result = run(["git", "pull", "--ff-only"])
            print(result.stdout, end="")
            if result.returncode == 0:
                if "Already up to date" in result.stdout:
                    ok("git pull: already up to date")
                else:
                    fixed("git pull updated the checkout")
            else:
                print(result.stderr, end="")
                fail("git pull failed — resolve manually, then rerun")
else:
    warn("not a git checkout — skipping git checks")

# ---------------------------------------------------------------- django settings
section("Django settings")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safari_backend.settings")
sys.path.insert(0, str(APP_DIR))
try:
    django.setup()
    from django.conf import settings
except Exception as exc:
    fail(f"could not load Django settings: {exc}")
    sys.exit(1)

static_root = Path(settings.STATIC_ROOT)
manifest_path = static_root / "staticfiles.json"
print(f"  STATIC_ROOT  : {static_root}")
print(f"  DEBUG        : {settings.DEBUG}")
print(f"  storage      : {settings.STORAGES['staticfiles']['BACKEND']}")

# ---------------------------------------------------------------- static files
section("Static files")

STATIC_TAG = re.compile(r"""{%\s*static\s+["']([^"']+)["']\s*%}""")


def template_static_refs():
    refs = set()
    for tpl in APP_DIR.rglob("templates/**/*.html"):
        refs.update(STATIC_TAG.findall(tpl.read_text(errors="ignore")))
    return refs


def manifest_missing():
    """Refs the templates use that the collectstatic manifest doesn't know."""
    if not manifest_path.exists():
        return None
    entries = json.loads(manifest_path.read_text()).get("paths", {})
    return sorted(r for r in template_static_refs() if r not in entries)


def run_collectstatic():
    if DRY_RUN:
        would("collectstatic")
        return
    from django.core.management import call_command
    try:
        call_command("collectstatic", interactive=False, verbosity=1)
        fixed(f"collectstatic regenerated {manifest_path}")
    except Exception as exc:
        fail(f"collectstatic failed: {exc}")


missing = manifest_missing()
if missing is None:
    warn(f"no manifest at {manifest_path} — collectstatic has never run for this checkout")
    run_collectstatic()
elif missing:
    warn("templates reference static files missing from the manifest:")
    for ref in missing:
        print(f"          {ref}")
    from django.contrib.staticfiles import finders
    need_collect = False
    for ref in missing:
        if finders.find(ref):
            need_collect = True
        else:
            fail(f"source file for '{ref}' not in the repo — git pull / merge the branch that adds it, then rerun")
    if need_collect:
        run_collectstatic()
else:
    ok("all template-referenced static files are in the manifest")

if changed and not DRY_RUN:
    still_missing = manifest_missing()
    if still_missing is None:
        fail(f"manifest still absent at {manifest_path} after collectstatic")
    elif still_missing:
        fail(f"still missing after collectstatic: {', '.join(still_missing)}")
    else:
        ok("post-fix verification: manifest now covers all template references")

# ---------------------------------------------------------------- migrations
section("Migrations")
try:
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(connections["default"])
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
except Exception as exc:
    fail(f"could not inspect migrations (database reachable?): {exc}")
    plan = None

if plan is None:
    pass
elif not plan:
    ok("no unapplied migrations")
elif DRY_RUN:
    would(f"manage.py migrate ({len(plan)} unapplied migration(s))")
else:
    from django.core.management import call_command
    try:
        call_command("migrate", interactive=False, verbosity=1)
        fixed(f"applied {len(plan)} pending migration(s)")
    except Exception as exc:
        fail(f"migrate failed: {exc}")

# ---------------------------------------------------------------- restart
section("Restart")
restart_file = APP_DIR / "tmp" / "restart.txt"
if pending:
    would("touch tmp/restart.txt (Passenger reload)")
elif changed:
    try:
        restart_file.parent.mkdir(exist_ok=True)
        restart_file.touch()
        fixed("touched tmp/restart.txt (Passenger will reload the app)")
    except OSError as exc:
        fail(f"could not touch {restart_file} ({exc}) — restart the app from cPanel")
else:
    skip("nothing changed — no restart needed")

print(flush=True)
if failed:
    print("RESULT: problems remain — see [FAIL] lines above.")
    sys.exit(1)
elif pending:
    print("RESULT: dry run — rerun without --dry-run to apply the [WOULD] items.")
elif changed:
    print("RESULT: fixes applied. Reload the site to confirm.")
else:
    print("RESULT: everything already in order. Nothing to do.")
