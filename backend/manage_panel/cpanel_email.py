"""Thin, safe wrapper around cPanel's local `uapi` CLI for managing mailboxes.

This only works when Django is actually running on the cPanel account itself
(production) — `uapi` is a local binary available to the account's own OS
user, not a network API, so there's nothing to configure locally; it simply
isn't available in local dev.
"""
import re
import secrets
import shutil
import string
import subprocess

COMPANY_EMAIL_DOMAIN = 'successfulluxurysafaris.co.ke'
LOCAL_PART_RE = re.compile(r'^[a-z0-9][a-z0-9._-]{0,63}$')


class CpanelUnavailable(Exception):
    """Raised when the uapi binary isn't available (e.g. local dev)."""


class CpanelError(Exception):
    """Raised when uapi ran but reported an error (e.g. duplicate mailbox)."""


def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _run(func, **params):
    if not shutil.which('uapi'):
        raise CpanelUnavailable("Email account management is only available on the live server.")
    args = ['uapi', '--output=json', 'Email', func] + [f'{k}={v}' for k, v in params.items()]
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=20,
            encoding='utf-8', errors='replace',
        )
    except FileNotFoundError:
        raise CpanelUnavailable("Email account management is only available on the live server.")
    import json
    try:
        data = json.loads(result.stdout)
    except ValueError:
        raise CpanelError(f"Unexpected response from the mail server: {result.stderr or result.stdout}")
    res = data.get('result', {})
    if res.get('status') != 1:
        errors = res.get('errors') or ['Unknown error']
        raise CpanelError('; '.join(errors))
    return res.get('data')


def list_mailboxes(domain=COMPANY_EMAIL_DOMAIN):
    data = _run('list_pops', domain=domain) or []
    return [row for row in data if row.get('email', '').endswith(f'@{domain}')]


def create_mailbox(local_part, password, quota_mb=1024, domain=COMPANY_EMAIL_DOMAIN):
    if not LOCAL_PART_RE.match(local_part):
        raise CpanelError(
            "Use only lowercase letters, numbers, dots, underscores or hyphens, starting with a letter or number."
        )
    _run('add_pop', email=local_part, password=password, domain=domain, quota=quota_mb)


def delete_mailbox(email, domain=COMPANY_EMAIL_DOMAIN):
    local_part = email.split('@')[0]
    _run('delete_pop', email=local_part, domain=domain)


def set_mailbox_password(email, password, domain=COMPANY_EMAIL_DOMAIN):
    _run('passwd_pop', email=email, password=password, domain=domain)
