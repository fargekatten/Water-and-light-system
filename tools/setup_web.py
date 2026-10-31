"""Generate local-only credentials without putting passwords in shell history."""
import getpass
import json
import os
from pathlib import Path
import secrets
from werkzeug.security import generate_password_hash

path = Path('instance/web.json')
if path.exists():
    raise SystemExit('instance/web.json finnes allerede; sikkerhetskopier/fjern den bevisst før passordbytte.')
password = getpass.getpass('Velg et unikt webpassord (minst 14 tegn): ')
if len(password) < 14 or password != getpass.getpass('Gjenta passordet: '):
    raise SystemExit('For kort passord eller passordene er ulike.')
path.parent.mkdir(mode=0o700, exist_ok=True)
with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as file:
    file.write(json.dumps(dict(secret_key=secrets.token_urlsafe(48),
                              password_hash=generate_password_hash(password))))
path.chmod(0o600)
print('Lokal konfigurasjon opprettet. Start python webapp.py --demo for en trygg demonstrasjon.')
