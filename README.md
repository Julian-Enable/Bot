# Bot de commits diarios (mantener el gráfico de contribuciones verde)

Este repositorio contiene una GitHub Action y un script que generan un commit diario para que aparezca como contribución en tu perfil.

> Aviso: para que las contribuciones aparezcan asociadas a tu cuenta, debes usar un Personal Access Token (PAT) de tu cuenta y configurar el nombre/email del autor con los que GitHub te reconoce. Automatizar commits puede afectar la representación real de tu actividad; úsalo con responsabilidad.

## Qué incluye

- `.github/workflows/daily-commit.yml` — workflow que se ejecuta diariamente (cron) y puede ejecutarse manualmente.
- `scripts/daily_commit.py` — script que añade una línea con la fecha en `contributions/keep_alive.md`, hace commit y push.

## Requisitos

1. Crear un Personal Access Token (PAT) con al menos scope `repo` (repo: status, repo_deployment, public_repo, repo:invite) para repositorios privados; para repos públicos puede bastar `public_repo`.
2. Añadir los siguientes secretos en el repositorio: `PAT`, `COMMIT_NAME`, `COMMIT_EMAIL`.
   - Ve a Settings → Secrets and variables → Actions → New repository secret.
   - `COMMIT_NAME` y `COMMIT_EMAIL` deben coincidir con los datos de tu cuenta GitHub (o con un email asociado a tu perfil) para que la contribución se atribuya correctamente.

## Cómo probar

1. Añade los secretos mencionados.
2. En GitHub, abre la pestaña Actions → el workflow `Daily commit to keep contributions green` y pulsa "Run workflow" (workflow_dispatch).
3. Espera a que termine la ejecución. Si todo va bien verás un nuevo commit en la rama por defecto y en tu perfil.

## Notas y mejoras

- El workflow actual realiza un commit diario en la rama que dispara el workflow (por defecto la rama principal donde esté el cron configurado).
- Puedes ajustar la hora del cron editando `.github/workflows/daily-commit.yml`.
- Para evitar commits múltiples el mismo día puedes mejorar el script para chequear la última línea del archivo o la fecha del último commit.

Non-intrusive / comportamiento por defecto

Este setup usa por defecto una rama separada llamada `contrib-bot` para que los commits del bot no modifiquen la rama principal ni el código en producción. Puedes cambiar la rama creando un secret `BOT_BRANCH` con otro nombre si lo deseas.

El script ya evita crear más de un commit por día (UTC) revisando la última entrada en `contributions/keep_alive.md`.

## Seguridad

- Mantén tu PAT privado. No lo subas al repositorio.
- Revoca el PAT si ya no lo usas.