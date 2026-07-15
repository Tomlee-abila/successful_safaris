#!/usr/bin/env bash
# server_doctor.sh — diagnose and fix the deployed Django app (static files, manifest, restart).
#
# Idempotent: every step checks current state first and only acts when needed.
# Run it from anywhere; it always operates on the checkout it lives in:
#
#   bash /home/slnkhczw/repositories/successful_safaris/backend/server_doctor.sh
#
# Options:
#   --pull      also run `git pull` in this checkout before checking
#   --dry-run   report problems but change nothing

set -u

DRY_RUN=0
DO_PULL=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --pull)    DO_PULL=1 ;;
        *) echo "Unknown option: $arg"; exit 2 ;;
    esac
done

CHANGED=0
FAILED=0
PENDING=0   # fixes that would run, but were skipped by --dry-run

ok()   { echo "  [OK]    $*"; }
fix()  { echo "  [FIXED] $*"; CHANGED=1; }
skip() { echo "  [SKIP]  $*"; }
pend() { echo "  [WOULD] $*"; PENDING=1; }
warn() { echo "  [WARN]  $*"; }
fail() { echo "  [FAIL]  $*"; FAILED=1; }

# ---------------------------------------------------------------- location
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Environment =="
echo "  invoked from : $(pwd)"
echo "  app dir      : $APP_DIR"
echo "  user/host    : $(whoami)@$(hostname)"

if [ ! -f "$APP_DIR/manage.py" ]; then
    fail "manage.py not found next to this script — is the script inside backend/?"
    exit 1
fi
cd "$APP_DIR"

# Warn if another checkout of the same project exists under $HOME (the
# two-checkout trap: running collectstatic in the wrong copy does nothing).
OTHER=$(find "$HOME" -maxdepth 3 -name passenger_wsgi.py -not -path "$APP_DIR/*" 2>/dev/null | head -3)
if [ -n "$OTHER" ]; then
    warn "other checkout(s) found — make sure the WSGI app points at THIS one:"
    echo "$OTHER" | sed 's/^/          /'
fi

# ---------------------------------------------------------------- python
echo "== Python =="
PYTHON=""
if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    PYTHON="$VIRTUAL_ENV/bin/python"
else
    # cPanel convention: $HOME/virtualenv/<path of app relative to $HOME>/<pyver>/bin/python
    REL="${APP_DIR#"$HOME"/}"
    for cand in "$HOME/virtualenv/$REL"/*/bin/python "$APP_DIR/venv/bin/python"; do
        if [ -x "$cand" ]; then PYTHON="$cand"; break; fi
    done
fi
[ -z "$PYTHON" ] && PYTHON="$(command -v python3 || true)"
if [ -z "$PYTHON" ]; then
    fail "no python interpreter found"
    exit 1
fi
PYVER=$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo "  python       : $PYTHON (Python $PYVER)"

# Django 5.x needs Python >= 3.10; refuse to "fix" things with the wrong interpreter.
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    fail "Python $PYVER is too old for this project (needs >= 3.10)."
    echo "          Look for the right one under: $HOME/virtualenv/${APP_DIR#"$HOME"/}/"
    exit 1
fi
ok "Python version is supported"

# ---------------------------------------------------------------- dependencies
echo "== Dependencies =="
if "$PYTHON" -c "import django, whitenoise, dotenv" 2>/dev/null; then
    ok "core packages importable (django, whitenoise, dotenv)"
else
    if [ ! -f "$APP_DIR/requirements.txt" ]; then
        fail "packages missing and no requirements.txt to install from"
        exit 1
    elif [ "$DRY_RUN" = 1 ]; then
        pend "pip install -r requirements.txt"
    elif "$PYTHON" -m pip install -r "$APP_DIR/requirements.txt"; then
        fix "installed dependencies from requirements.txt"
    else
        fail "pip install failed — check the output above"
        exit 1
    fi
fi
if [ "$DRY_RUN" = 1 ] && ! "$PYTHON" -c "import django" 2>/dev/null; then
    fail "django not importable; later checks can't run in dry-run without it"
    exit 1
fi

# ---------------------------------------------------------------- git
echo "== Git =="
if [ -d "$APP_DIR/../.git" ] || git -C "$APP_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    echo "  branch       : $(git -C "$APP_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    echo "  commit       : $(git -C "$APP_DIR" log --oneline -1 2>/dev/null)"
    if [ "$DO_PULL" = 1 ]; then
        if [ "$DRY_RUN" = 1 ]; then
            pend "git pull"
        else
            if git -C "$APP_DIR" pull --ff-only; then
                fix "git pull"
            else
                fail "git pull failed — resolve manually, then rerun"
            fi
        fi
    fi
else
    warn "not a git checkout — skipping git checks"
fi

# ---------------------------------------------------------------- django settings
echo "== Django settings =="
SETTINGS_INFO=$("$PYTHON" - <<'PY' 2>&1
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safari_backend.settings")
import django
django.setup()
from django.conf import settings
print(f"STATIC_ROOT={settings.STATIC_ROOT}")
print(f"DEBUG={settings.DEBUG}")
print(f"STORAGE={settings.STORAGES['staticfiles']['BACKEND']}")
PY
)
if ! echo "$SETTINGS_INFO" | grep -q '^STATIC_ROOT='; then
    fail "could not load Django settings:"
    echo "$SETTINGS_INFO" | sed 's/^/          /'
    exit 1
fi
echo "$SETTINGS_INFO" | sed 's/^/  /'
STATIC_ROOT=$(echo "$SETTINGS_INFO" | sed -n 's/^STATIC_ROOT=//p')
MANIFEST="$STATIC_ROOT/staticfiles.json"

# ---------------------------------------------------------------- static files
echo "== Static files =="

# Every {% static 'literal' %} referenced by the templates must exist in the
# collectstatic manifest, or ManifestStaticFilesStorage 500s at render time.
MISSING=$("$PYTHON" - "$APP_DIR" "$MANIFEST" <<'PY'
import json, re, sys
from pathlib import Path

app_dir, manifest_path = Path(sys.argv[1]), Path(sys.argv[2])

refs = set()
pattern = re.compile(r"""{%\s*static\s+["']([^"']+)["']\s*%}""")
for tpl in app_dir.rglob("templates/**/*.html"):
    refs.update(pattern.findall(tpl.read_text(errors="ignore")))

if not manifest_path.exists():
    print("__NO_MANIFEST__")
    sys.exit(0)

entries = json.loads(manifest_path.read_text()).get("paths", {})
for ref in sorted(refs):
    if ref not in entries:
        print(ref)
PY
)

run_collectstatic() {
    if [ "$DRY_RUN" = 1 ]; then
        pend "collectstatic"
    elif "$PYTHON" manage.py collectstatic --noinput; then
        fix "collectstatic regenerated $MANIFEST"
    else
        fail "collectstatic failed"
    fi
}

if [ "$MISSING" = "__NO_MANIFEST__" ]; then
    warn "no manifest at $MANIFEST — collectstatic has never run for this checkout"
    run_collectstatic
elif [ -n "$MISSING" ]; then
    warn "templates reference static files missing from the manifest:"
    echo "$MISSING" | sed 's/^/          /'
    # Distinguish "source file missing from repo" from "just needs collectstatic"
    NEED_COLLECT=0
    while IFS= read -r ref; do
        if [ -f "$APP_DIR/static/$ref" ] || ls "$APP_DIR"/*/static/"$ref" >/dev/null 2>&1; then
            NEED_COLLECT=1
        else
            fail "source file for '$ref' not in the repo — git pull / merge the branch that adds it, then rerun"
        fi
    done <<< "$MISSING"
    [ "$NEED_COLLECT" = 1 ] && run_collectstatic
else
    ok "all template-referenced static files are in the manifest"
fi

# Re-verify after a fix
if [ "$CHANGED" = 1 ] && [ "$DRY_RUN" = 0 ] && [ -f "$MANIFEST" ]; then
    STILL_MISSING=$("$PYTHON" - "$APP_DIR" "$MANIFEST" <<'PY'
import json, re, sys
from pathlib import Path
app_dir, manifest_path = Path(sys.argv[1]), Path(sys.argv[2])
pattern = re.compile(r"""{%\s*static\s+["']([^"']+)["']\s*%}""")
refs = set()
for tpl in app_dir.rglob("templates/**/*.html"):
    refs.update(pattern.findall(tpl.read_text(errors="ignore")))
entries = json.loads(manifest_path.read_text()).get("paths", {})
print("\n".join(sorted(r for r in refs if r not in entries)))
PY
)
    if [ -z "$STILL_MISSING" ]; then
        ok "post-fix verification: manifest now covers all template references"
    else
        fail "still missing after collectstatic: $STILL_MISSING"
    fi
fi

# ---------------------------------------------------------------- migrations
echo "== Migrations =="
if "$PYTHON" manage.py migrate --check >/dev/null 2>&1; then
    ok "no unapplied migrations"
elif [ "$DRY_RUN" = 1 ]; then
    pend "manage.py migrate (unapplied migrations detected)"
elif "$PYTHON" manage.py migrate --noinput; then
    fix "applied pending migrations"
else
    fail "migrate failed — check the output above"
fi

# ---------------------------------------------------------------- restart
echo "== Restart =="
if [ "$PENDING" = 1 ]; then
    pend "touch tmp/restart.txt (Passenger reload)"
elif [ "$CHANGED" = 1 ]; then
    mkdir -p "$APP_DIR/tmp" && touch "$APP_DIR/tmp/restart.txt" \
        && fix "touched tmp/restart.txt (Passenger will reload the app)" \
        || fail "could not touch $APP_DIR/tmp/restart.txt — restart the app from cPanel"
else
    skip "nothing changed — no restart needed"
fi

echo
if [ "$FAILED" = 1 ]; then
    echo "RESULT: problems remain — see [FAIL] lines above."
    exit 1
elif [ "$PENDING" = 1 ]; then
    echo "RESULT: dry run — rerun without --dry-run to apply the [WOULD] items."
elif [ "$CHANGED" = 1 ]; then
    echo "RESULT: fixes applied. Reload the site to confirm."
else
    echo "RESULT: everything already in order. Nothing to do."
fi
