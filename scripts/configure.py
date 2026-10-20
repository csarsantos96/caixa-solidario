"""Generate local credentials without modifying an existing configuration."""
from pathlib import Path
import os
import secrets

root = Path(__file__).resolve().parents[1]
path = root / ".env"
password = secrets.token_urlsafe(24)
db_password = secrets.token_urlsafe(24)
text = (root / ".env.example").read_text().replace("ADMIN_PASSWORD=", "ADMIN_PASSWORD=" + password, 1).replace("POSTGRES_PASSWORD=", "POSTGRES_PASSWORD=" + db_password, 1)
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env já existe. Nenhuma alteração foi feita. Consulte sua configuração atual.")
with os.fdopen(fd, "w") as file:
    file.write(text)
print("Configuração criada. Não envie .env para o GitHub.")
print("Usuário: admin")
print("Senha:", password)
print("Guarde a senha. Para iniciar: docker compose up --build -d")
