# Bot de commits diarios (mantener el gráfico de contribuciones verde)

Este repositorio contiene una GitHub Action y un script que generan un commit diario para que aparezca como contribución en tu perfil de GitHub.

> Aviso: para que las contribuciones aparezcan asociadas a tu cuenta, debes usar un Personal Access Token (PAT) de tu cuenta y configurar el nombre/email del autor con los que GitHub te reconoce. Automatizar commits puede afectar la representación real de tu actividad; úsalo con responsabilidad.

## Qué incluye

- `.github/workflows/daily-commit.yml` — workflow que se ejecuta 2 veces al día (09:00 y 18:00 UTC) y puede ejecutarse manualmente.
- `scripts/daily_commit.py` — script que crea un archivo `.md` con la fecha en `contributions/YYYY/MM/DD/`, hace commit y push a la rama `contrib-bot`.

## Requisitos

1. Crear un Personal Access Token (PAT) con al menos scope `repo` para repositorios privados; para repos públicos puede bastar `public_repo`.
2. Añadir los siguientes secretos en el repositorio: `PAT`, `COMMIT_NAME`, `COMMIT_EMAIL`.
   - Ve a Settings → Secrets and variables → Actions → New repository secret.
   - `COMMIT_NAME` y `COMMIT_EMAIL` deben coincidir con los datos de tu cuenta GitHub (o con un email asociado a tu perfil) para que la contribución se atribuya correctamente.

## Cómo probar

1. Añade los secretos mencionados.
2. En GitHub, abre la pestaña Actions → el workflow `Daily contribution bot` y pulsa "Run workflow" (`workflow_dispatch`).
3. Espera a que termine la ejecución. Si todo va bien verás un nuevo commit en la rama `contrib-bot` y en tu perfil.

## Notas

- El workflow ejecuta el script **2 veces al día** (09:00 y 18:00 UTC), creando como máximo **1 commit por ejecución** → máximo 2 commits diarios.
- Puedes ajustar las horas del cron editando `.github/workflows/daily-commit.yml`.
- El script usa la rama `contrib-bot` por defecto para que los commits del bot no modifiquen la rama `master`.
- Puedes cambiar la rama creando el secreto `BOT_BRANCH` con otro nombre.
- El script verifica si ya existe un archivo `.md` en `contributions/YYYY/MM/DD/` antes de crear uno nuevo, evitando commits múltiples el mismo día.
- Si el push falla, el script reintenta hasta 3 veces.

## Seguridad

- Mantén tu PAT privado. No lo subas al repositorio.
- Revoca el PAT si ya no lo usas.
