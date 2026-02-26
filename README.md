# commit-watcher-agent

Monitoriza un repositorio público de GitHub y, cuando aparece un commit nuevo, genera un resumen técnico con OpenAI y lo envía por correo a una o varias personas.

## Estructura

- `.github/workflows/monitor.yml`: workflow con cron para ejecutar el monitor.
- `scripts/check_and_notify.py`: script principal.
- `scripts/send_email.py`: helper opcional para probar envío SMTP.
- `last_sha.txt`: SHA ya procesado para evitar duplicados.

## Secrets y variables recomendadas

Configura estos *Repository secrets* en GitHub:

- `GITHUB_TOKEN_CUSTOM`
- `OPENAI_API_KEY`
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`

Y ajusta en el workflow:

- `TARGET_OWNER`
- `TARGET_REPO`
- `EMAIL_TO_LIST`

## Uso local

```bash
pip install requests
export TARGET_OWNER="owner_del_repo_publico"
export TARGET_REPO="nombre_del_repo_publico"
export GITHUB_TOKEN_CUSTOM="..."
export OPENAI_API_KEY="..."
export EMAIL_USERNAME="..."
export EMAIL_PASSWORD="..."
export EMAIL_TO_LIST="uno@correo.com,dos@correo.com"
python3 scripts/check_and_notify.py
```

## Nota

Si el diff de un commit es demasiado grande, considera recortarlo por tipo de archivo o tamaño antes de enviarlo al modelo.
