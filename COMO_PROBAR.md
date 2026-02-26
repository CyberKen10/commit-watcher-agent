# Cómo probar el commit watcher

Este documento explica cómo validar que el monitor funciona correctamente con **Gmail SMTP**.

## 0) Requisito obligatorio para Gmail

Antes de probar envío de correo:

1. Activa 2FA en Google.
2. Crea un **App Password** de Gmail (16 caracteres).
3. Usa ese valor en `EMAIL_PASSWORD`.

> Gmail normalmente bloquea usuario+contraseña normal en SMTP; usa App Password.

## 1) Prueba local del monitor

Instala dependencias:

```bash
pip install requests
```

Configura variables mínimas:

```bash
export TARGET_OWNER="owner_del_repo_publico"
export TARGET_REPO="nombre_del_repo_publico"
export GH_TOKEN_CUSTOM="tu_token_github"
export OPENAI_API_KEY="tu_openai_api_key"
export EMAIL_PASSWORD="tu_app_password_de_gmail"
# opcional: export EMAIL_USERNAME="kendryjavierdelpino@gmail.com"
# opcional: export EMAIL_TO_LIST="destino1@correo.com,destino2@correo.com"
```

Ejecuta:

```bash
python3 scripts/check_and_notify.py
```

Resultado esperado:

- Si hay commit nuevo: imprime `Nuevo commit detectado`, genera resumen y guarda SHA en `last_sha.txt`.
- Si no hay commit nuevo: imprime `No hay commits nuevos`.
- Si falta `EMAIL_PASSWORD`: imprime aviso y salta el envío.

## 2) Prueba directa de envío de correo (SMTP Gmail)

Configura:

```bash
export EMAIL_USERNAME="kendryjavierdelpino@gmail.com"
export EMAIL_PASSWORD="tu_app_password_de_gmail"
export EMAIL_TO_LIST="destino1@correo.com,destino2@correo.com"
```

Lanza helper:

```bash
python3 scripts/send_email.py "Prueba" "Correo de prueba del commit watcher"
```

Resultado esperado: llega un correo con el asunto y contenido indicados.

## 3) Probar workflow de GitHub Actions

1. Sube los cambios al repositorio.
2. En GitHub, configura estos **Repository secrets**:
   - `GH_TOKEN_CUSTOM`
   - `OPENAI_API_KEY`
   - `EMAIL_PASSWORD` (App Password)
3. Opcionalmente agrega:
   - `EMAIL_USERNAME` (si quieres otro remitente)
   - `EMAIL_TO_LIST`
4. Edita `.github/workflows/monitor.yml` si necesitas cambiar:
   - `TARGET_OWNER`
   - `TARGET_REPO`
5. Ve a **Actions** → workflow **Monitor public repo and send commit summary**.
6. Ejecuta **Run workflow** manualmente.

Resultado esperado: el job finaliza en verde, el script procesa el commit nuevo (si existe), envía notificación por correo y, si cambió `last_sha.txt`, abre un PR automático.

## 4) Validaciones rápidas útiles

```bash
python3 -m py_compile scripts/check_and_notify.py scripts/send_email.py
```

```bash
cat last_sha.txt
```

- `py_compile` debe terminar sin errores.
- `last_sha.txt` debe contener el SHA más reciente procesado tras una ejecución con commit nuevo.

## 5) Problemas comunes

- **401/403 GitHub API**: revisa `GH_TOKEN_CUSTOM` y permisos.
- **401 OpenAI**: verifica `OPENAI_API_KEY`.
- **SMTP auth failed**: revisa que `EMAIL_PASSWORD` sea App Password de Gmail y que 2FA esté activa.
- **No llega correo**: revisa spam, dominio permitido y formato de `EMAIL_TO_LIST`.


## 6) Validar auto-commit / auto-PR de `last_sha.txt`

1. Ejecuta el workflow con un commit nuevo disponible en el repo monitoreado.
2. Verifica en logs que aparezca `Detected changes in last_sha.txt`.
3. Confirma que se creó un PR con título `chore: actualizar last_sha automáticamente`.
4. Confirma que el PR quedó **Approved** y con **auto-merge** habilitado (o mergeado).

Si no se aprueba/mergea solo, revisa que `GH_TOKEN_CUSTOM` tenga permisos para `contents` y `pull-requests`.
