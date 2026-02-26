# commit-watcher-agent

Monitoriza un repositorio público de GitHub y, cuando aparece un commit nuevo, genera un resumen técnico con OpenAI y lo envía por correo a una o varias personas.

## Estructura

- `.github/workflows/monitor.yml`: workflow con cron para ejecutar el monitor.
- `scripts/check_and_notify.py`: script principal.
- `scripts/send_email.py`: helper opcional para probar envío SMTP.
- `last_sha.txt`: SHA ya procesado para evitar duplicados.

## SMTP configurado para Gmail

El proyecto ya viene preparado para usar **Gmail SMTP**:

- Servidor: `smtp.gmail.com`
- Puerto: `587`
- TLS: `starttls()`
- Remitente por defecto: `kendryjavierdelpino@gmail.com`

> Si no defines `EMAIL_USERNAME`, se usa automáticamente `kendryjavierdelpino@gmail.com`.

## Qué tienes que hacer tú para que funcione

1. En tu cuenta de Google activa **2-Step Verification** (2FA).
2. Genera un **App Password** para Mail (clave de 16 caracteres).
3. Configura secretos/variables con ese App Password (no tu contraseña normal).

## Secrets y variables recomendadas

Configura estos *Repository secrets* en GitHub:

- `GH_TOKEN_CUSTOM`
- `OPENAI_API_KEY`
- `EMAIL_PASSWORD`  ← App Password de Gmail

Opcional:

- `EMAIL_USERNAME` (si quieres usar otro remitente distinto al default)
- `EMAIL_TO_LIST` (destinos separados por coma; por defecto usa `kendryjavierdelpino@gmail.com`)

Y ajusta en el workflow:

- `TARGET_OWNER`
- `TARGET_REPO`

## Uso local

```bash
pip install requests
export TARGET_OWNER="owner_del_repo_publico"
export TARGET_REPO="nombre_del_repo_publico"
export GH_TOKEN_CUSTOM="..."
export OPENAI_API_KEY="..."
export EMAIL_PASSWORD="app_password_de_gmail"
# opcional:
# export EMAIL_USERNAME="kendryjavierdelpino@gmail.com"
# export EMAIL_TO_LIST="uno@correo.com,dos@correo.com"
python3 scripts/check_and_notify.py
```

## Nota

Si el diff de un commit es demasiado grande, considera recortarlo por tipo de archivo o tamaño antes de enviarlo al modelo.
