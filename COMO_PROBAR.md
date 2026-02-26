# Cómo probar el commit watcher

Este documento explica cómo validar que el monitor funciona correctamente.

## 1) Prueba local (sin enviar correo real)

Instala dependencias:

```bash
pip install requests
```

Configura variables mínimas para consultar commits y generar resumen:

```bash
export TARGET_OWNER="owner_del_repo_publico"
export TARGET_REPO="nombre_del_repo_publico"
export GITHUB_TOKEN_CUSTOM="tu_token_github"
export OPENAI_API_KEY="tu_openai_api_key"
```

Opcionalmente evita envío real de email **no** configurando `EMAIL_USERNAME`/`EMAIL_PASSWORD`.

Ejecuta:

```bash
python3 scripts/check_and_notify.py
```

Resultado esperado:

- Si hay commit nuevo: imprime `Nuevo commit detectado`, genera resumen y guarda SHA en `last_sha.txt`.
- Si no hay commit nuevo: imprime `No hay commits nuevos`.

## 2) Prueba de envío de correo (SMTP)

Configura:

```bash
export EMAIL_USERNAME="tu_correo"
export EMAIL_PASSWORD="tu_password_o_app_password"
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
   - `GITHUB_TOKEN_CUSTOM`
   - `OPENAI_API_KEY`
   - `EMAIL_USERNAME`
   - `EMAIL_PASSWORD`
3. Edita `.github/workflows/monitor.yml` si necesitas cambiar:
   - `TARGET_OWNER`
   - `TARGET_REPO`
   - `EMAIL_TO_LIST`
4. Ve a **Actions** → workflow **Monitor public repo and send commit summary**.
5. Ejecuta **Run workflow** manualmente.

Resultado esperado: el job finaliza en verde y el script procesa el commit nuevo (si existe) y envía notificación por correo.

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

- **401/403 GitHub API**: revisa `GITHUB_TOKEN_CUSTOM` y permisos.
- **401 OpenAI**: verifica `OPENAI_API_KEY`.
- **SMTP auth failed**: en Gmail suele requerirse **App Password** y 2FA.
- **No llega correo**: revisa spam, dominio permitido y formato de `EMAIL_TO_LIST`.
